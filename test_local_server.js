const express = require('express');
const { spawn } = require('child_process');
const path = require('path');

const app = express();
const PORT = 3002;

// Servir les fichiers statiques
app.use(express.static('public'));

// API pour les métadonnées
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

  console.log('Exécution:', 'python3', args.join(' '));

  const py = spawn('python', args);
  let stdout = '';
  let stderr = '';

  py.stdout.on('data', (data) => {
    stdout += data.toString();
  });

  py.stderr.on('data', (data) => {
    stderr += data.toString();
  });

  const killTimer = setTimeout(() => {
    py.kill('SIGKILL');
  }, 15000);

  py.on('close', code => {
    clearTimeout(killTimer);

    if (code !== 0) {
      console.error('now-playing python error:', { code, stderr: stderr.slice(0, 2000) });
      return res.status(500).json({ error: 'Erreur metadata (python)', details: stderr.slice(0, 500) });
    }

    try {
      const payload = JSON.parse(stdout);
      console.log('Metadata retournées:', payload);
      return res.json(payload);
    } catch (e) {
      console.error('now-playing json parse error:', e, stdout.slice(0, 2000));
      return res.status(500).json({ error: 'Réponse metadata invalide', details: stdout.slice(0, 500) });
    }
  });
});

// API pour les radios (mock sans base de données)
app.get('/api/radios', (req, res) => {
  const mockRadios = [
    { id: 1, name: 'RTL', url: 'http://streaming.radio.rtl.fr/rtl-1-44-128', genre: 'Généraliste', logo_url: '' },
    { id: 2, name: '100% Radio', url: 'https://100radio-80.ice.infomaniak.ch/100radio-80-128.mp3', genre: '80s', logo_url: '' },
    { id: 3, name: 'Test Cover', url: 'https://example.com/test.mp3', genre: 'Test', logo_url: '' }
  ];
  res.json(mockRadios);
});

// Endpoints d'authentification (mock)
app.post('/api/login', (req, res) => {
  res.json({ success: true, message: 'Mock login' });
});

app.get('/api/auth-status', (req, res) => {
  res.json({ authenticated: true, user: { username: 'test' } });
});

// Favicon
app.get('/favicon.ico', (req, res) => {
  res.status(204).send();
});

app.listen(PORT, () => {
  console.log(`Serveur de test démarré sur http://localhost:${PORT}`);
  console.log('Testez les covers avec: http://localhost:' + PORT + '/test_cover_api.html');
});
