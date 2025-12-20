const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const compression = require('compression');
const path = require('path');
const dotenv = require('dotenv');
const { Pool } = require('pg');
const axios = require('axios');
const session = require('express-session');
const PgSession = require('connect-pg-simple')(session);
const bcrypt = require('bcryptjs');
const { createProxyMiddleware } = require('http-proxy-middleware');
const { spawn } = require('child_process');

dotenv.config();

const app = express();
const PORT = process.env.PORT || 3000;

// Configuration PostgreSQL
const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  ssl: process.env.NODE_ENV === 'production' ? { rejectUnauthorized: false } : false
});

// ---------- MIDDLEWARES ----------

app.use(
  helmet({
    contentSecurityPolicy: {
      useDefaults: true,
      directives: {
        "default-src": ["'self'"],
        "script-src": ["'self'"],
        "style-src": ["'self'", "'unsafe-inline'"],
        "img-src": ["'self'", "data:", "https:", "http:"],
        "connect-src": ["'self'"],
        // Autoriser les flux audio (mp3, etc.) depuis HTTPS ET HTTP
        "media-src": ["'self'", "https:", "http:", "data:"],
        "frame-ancestors": ["'self'"]
      }
    }
  })
);

app.use(compression());
app.use(cors());
app.use(express.json());
app.use(express.static('public'));

app.get('/favicon.ico', (req, res) => {
  return res.status(204).end();
});

// Proxy pour les flux audio HTTP (évite mixed content)
app.use('/proxy-stream', createProxyMiddleware({
  target: 'http://',
  changeOrigin: true,
  pathRewrite: {
    '^/proxy-stream/': '',
  },
  onProxyRes(proxyRes) {
    proxyRes.headers['access-control-allow-origin'] = '*';
  }
}));

// Sessions
app.use(
  session({
    store: new PgSession({
      pool,
      tableName: 'user_sessions'
    }),
    secret: process.env.SESSION_SECRET || 'dev-secret-change-me',
    resave: false,
    saveUninitialized: false,
    cookie: {
      secure: process.env.NODE_ENV === 'production',
      maxAge: 7 * 24 * 60 * 60 * 1000 // 7 jours
    }
  })
);

// Middleware de protection des routes admin
function requireAuth(req, res, next) {
  if (req.session && req.session.user) {
    return next();
  }
  return res.status(401).json({ error: 'Non autorisé' });
}

// ---------- ROUTES API RADIOS ----------

app.get('/api/radios', async (req, res) => {
  try {
    const result = await pool.query('SELECT * FROM radios ORDER BY name');
    res.json(result.rows);
  } catch (error) {
    console.error('Erreur:', error);
    res.status(500).json({ error: 'Erreur serveur' });
  }
});

app.post('/api/radios', requireAuth, async (req, res) => {
  const { name, url, description, genre } = req.body;
  try {
    const result = await pool.query(
      'INSERT INTO radios (name, url, description, genre) VALUES ($1, $2, $3, $4) RETURNING *',
      [name, url, description, genre]
    );
    res.json(result.rows[0]);
  } catch (error) {
    console.error('Erreur:', error);
    res.status(500).json({ error: 'Erreur serveur' });
  }
});

app.delete('/api/radios/:id', requireAuth, async (req, res) => {
  const { id } = req.params;
  try {
    await pool.query('DELETE FROM radios WHERE id = $1', [id]);
    res.json({ message: 'Radio supprimée' });
  } catch (error) {
    console.error('Erreur:', error);
    res.status(500).json({ error: 'Erreur serveur' });
  }
});

// ---------- METADONNÉES NOW-PLAYING (Python) ----------

app.get('/api/now-playing', async (req, res) => {
  const name = req.query.name;
  const url = req.query.url;

  if (!name || !url) {
    return res.status(400).json({ error: 'Paramètres requis: name, url' });
  }

  const scriptPath = path.join(__dirname, 'radio_metadata_fetcher_fixed.py');
  const args = [
    scriptPath,
    '--json',
    '--station',
    String(name),
    '--url',
    String(url)
  ];

  const pythonBin = process.env.PYTHON_BIN || '/app/venv/bin/python';

  const py = spawn(pythonBin, args, {
    stdio: ['ignore', 'pipe', 'pipe'],
    env: process.env
  });

  let stdout = '';
  let stderr = '';

  const killTimer = setTimeout(() => {
    try {
      py.kill('SIGKILL');
    } catch (e) {
      // ignore
    }
  }, 12000);

  py.stdout.on('data', chunk => {
    stdout += chunk.toString('utf8');
  });
  py.stderr.on('data', chunk => {
    stderr += chunk.toString('utf8');
  });

  py.on('close', code => {
    clearTimeout(killTimer);

    if (code !== 0) {
      console.error('now-playing python error:', { code, stderr: stderr.slice(0, 2000) });
      return res.status(500).json({ error: 'Erreur metadata (python)', details: stderr.slice(0, 500) });
    }

    try {
      const payload = JSON.parse(stdout);
      return res.json(payload);
    } catch (e) {
      console.error('now-playing json parse error:', e, stdout.slice(0, 2000));
      return res.status(500).json({ error: 'Réponse metadata invalide', details: stdout.slice(0, 500) });
    }
  });
});

app.get('/api/debug/nostalgie-onair', async (req, res) => {
  try {
    const r = await axios.get('https://www.nostalgie.fr/onair.json', {
      timeout: 10000,
      headers: {
        'User-Agent': 'Mozilla/5.0',
        'Accept': 'application/json, text/plain, */*',
        'Referer': 'https://www.nostalgie.fr/'
      },
      responseType: 'text',
      validateStatus: () => true
    });

    const text = typeof r.data === 'string' ? r.data : JSON.stringify(r.data);
    return res.json({
      status: r.status,
      contentType: r.headers ? (r.headers['content-type'] || null) : null,
      head: text.slice(0, 300)
    });
  } catch (e) {
    return res.status(500).json({
      error: String(e && e.message ? e.message : e),
      code: e && e.code ? e.code : null
    });
  }
});

// ---------- VALIDATION DES URLS DE STREAMING ----------
// Utilise GET en mode stream (HEAD est souvent refusé par les serveurs de radio)

app.get('/api/validate-stream/:url', async (req, res) => {
  const { url } = req.params;
  try {
    const response = await axios.get(url, {
      method: 'GET',
      responseType: 'stream',
      timeout: 7000,
      maxContentLength: 1024 * 50 // 50 Ko max
    });

    res.json({
      valid: true,
      contentType: response.headers['content-type'] || null
    });
  } catch (error) {
    console.error('validate-stream error:', error.message);
    res.json({ valid: false, error: error.message });
  }
});

// ---------- ROUTES AUTH ----------

app.post('/api/login', async (req, res) => {
  const { username, password } = req.body || {};
  if (!username || !password) {
    return res.status(400).json({ error: 'Nom d’utilisateur et mot de passe requis' });
  }

  try {
    const result = await pool.query('SELECT * FROM admins WHERE username = $1', [username]);
    const admin = result.rows[0];

    if (!admin) {
      return res.status(401).json({ error: 'Identifiants invalides' });
    }

    const match = await bcrypt.compare(password, admin.password_hash);
    if (!match) {
      return res.status(401).json({ error: 'Identifiants invalides' });
    }

    req.session.user = { id: admin.id, username: admin.username };
    res.json({ success: true, username: admin.username });
  } catch (error) {
    console.error('Erreur login:', error);
    res.status(500).json({ error: 'Erreur serveur' });
  }
});

app.post('/api/logout', (req, res) => {
  req.session.destroy(err => {
    if (err) {
      console.error('Erreur logout:', err);
      return res.status(500).json({ error: 'Erreur de déconnexion' });
    }
    res.clearCookie('connect.sid');
    res.json({ success: true });
  });
});

app.get('/api/auth-status', (req, res) => {
  if (req.session && req.session.user) {
    return res.json({ authenticated: true, username: req.session.user.username });
  }
  return res.json({ authenticated: false });
});

// ---------- ROUTE PRINCIPALE ----------

app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

// ---------- INITIALISATION DE LA BASE DE DONNÉES ----------

async function initDB() {
  try {
    // Table radios
    await pool.query(`
      CREATE TABLE IF NOT EXISTS radios (
        id SERIAL PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        url VARCHAR(500) NOT NULL UNIQUE,
        description TEXT,
        genre VARCHAR(100),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        is_active BOOLEAN DEFAULT true
      )
    `);

    // Table admins
    await pool.query(`
      CREATE TABLE IF NOT EXISTS admins (
        id SERIAL PRIMARY KEY,
        username VARCHAR(100) UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
      )
    `);

    // Table sessions (pour connect-pg-simple)
    await pool.query(`
      CREATE TABLE IF NOT EXISTS user_sessions (
        sid varchar NOT NULL COLLATE "default",
        sess json NOT NULL,
        expire timestamp(6) NOT NULL
      )
    `);

    // Index pour les sessions (si pas déjà créé)
    await pool.query(`
      DO $$
      BEGIN
        IF NOT EXISTS (
          SELECT 1 FROM pg_class c
          JOIN pg_namespace n ON n.oid = c.relnamespace
          WHERE c.relname = 'user_sessions_pkey'
        ) THEN
          ALTER TABLE user_sessions ADD CONSTRAINT user_sessions_pkey PRIMARY KEY (sid);
        END IF;
      END$$;
    `);

    // Créer un admin par défaut si aucun n'existe
    const adminsCount = await pool.query('SELECT COUNT(*) FROM admins');
    if (parseInt(adminsCount.rows[0].count, 10) === 0) {
      const defaultUsername = 'admin';
      const defaultPassword = 'admin123'; // À changer après la première connexion
      const hash = await bcrypt.hash(defaultPassword, 10);

      await pool.query(
        'INSERT INTO admins (username, password_hash) VALUES ($1, $2)',
        [defaultUsername, hash]
      );

      console.log('Admin par défaut créé :', defaultUsername, '/', defaultPassword);
    }

    console.log('Base de données initialisée');
  } catch (error) {
    console.error('Erreur DB:', error);
  }
}

// ---------- DÉMARRAGE SERVEUR ----------

app.listen(PORT, async () => {
  await initDB();
  let dbHost = '';
  try {
    const u = new URL(process.env.DATABASE_URL || '');
    dbHost = u.host;
  } catch (e) {
    dbHost = '';
  }

  console.log('Serveur démarré');
  console.log('PORT:', PORT);
  if (dbHost) console.log('DB host:', dbHost);
});