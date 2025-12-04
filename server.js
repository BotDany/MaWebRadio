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

dotenv.config();

const app = express();
const PORT = process.env.PORT || 3000;

// Configuration PostgreSQL
const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  ssl: process.env.NODE_ENV === 'production' ? { rejectUnauthorized: false } : false
});

// Middlewares
app.use(helmet());
app.use(compression());
app.use(cors());
app.use(express.json());
app.use(express.static('public'));

// Routes API
app.get('/api/radios', async (req, res) => {
  try {
    const result = await pool.query('SELECT * FROM radios ORDER BY name');
    res.json(result.rows);
  } catch (error) {
    console.error('Erreur:', error);
    res.status(500).json({ error: 'Erreur serveur' });
  }
});

app.post('/api/radios', async (req, res) => {
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

app.delete('/api/radios/:id', async (req, res) => {
  const { id } = req.params;
  try {
    await pool.query('DELETE FROM radios WHERE id = $1', [id]);
    res.json({ message: 'Radio supprimée' });
  } catch (error) {
    console.error('Erreur:', error);
    res.status(500).json({ error: 'Erreur serveur' });
  }
});

// Validation des URLs de streaming
app.get('/api/validate-stream/:url', async (req, res) => {
  const { url } = req.params;
  try {
    const response = await axios.head(url, { timeout: 5000 });
    res.json({ valid: true, contentType: response.headers['content-type'] });
  } catch (error) {
    res.json({ valid: false, error: error.message });
  }
});

// Route principale
app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

// Initialisation de la base de données
async function initDB() {
  try {
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
    console.log('Base de données initialisée');
  } catch (error) {
    console.error('Erreur DB:', error);
  }
}

// Démarrage serveur
app.listen(PORT, async () => {
  await initDB();
  console.log(`Serveur démarré sur http://localhost:${PORT}`);
});