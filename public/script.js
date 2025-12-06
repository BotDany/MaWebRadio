document.addEventListener('DOMContentLoaded', () => {
    const audioPlayer = document.getElementById('audio-player');
    const playBtn = document.getElementById('play-btn');
    const stopBtn = document.getElementById('stop-btn');
    const volumeControl = document.getElementById('volume');
    const radioStationsList = document.getElementById('radio-stations');
    const addRadioBtn = document.getElementById('add-radio');
    const radioNameInput = document.getElementById('radio-name');
    const radioUrlInput = document.getElementById('radio-url');
    const radioGenreInput = document.getElementById('radio-genre');
    const currentRadioDisplay = document.getElementById('current-radio');
    const nowPlayingCover = document.getElementById('now-playing-cover');

    const loginForm = document.getElementById('login-form');
    const adminPanel = document.getElementById('admin-panel');
    const adminUsername = document.getElementById('admin-username');
    const loginBtn = document.getElementById('login-btn');
    const logoutBtn = document.getElementById('logout-btn');

    const playerContainer = document.querySelector('.player');
    const adminRadiosSection = document.getElementById('admin-radios');

    let currentRadio = null;

    // ---------- AUTH ----------

    async function checkAuth() {
        try {
            const response = await fetch('/api/auth-status');

            if (!response.ok) {
                console.error('Auth status HTTP error:', response.status);
                loginForm.style.display = 'block';
                adminPanel.style.display = 'none';
                if (adminRadiosSection) adminRadiosSection.style.display = 'none';
                return;
            }

            const data = await response.json();

            if (data.authenticated) {
                loginForm.style.display = 'none';
                adminPanel.style.display = 'flex';
                adminUsername.textContent = data.username;
                if (adminRadiosSection) adminRadiosSection.style.display = 'block';
            } else {
                loginForm.style.display = 'block';
                adminPanel.style.display = 'none';
                if (adminRadiosSection) adminRadiosSection.style.display = 'none';
            }
        } catch (error) {
            console.error('Erreur auth:', error);
            loginForm.style.display = 'block';
            adminPanel.style.display = 'none';
            if (adminRadiosSection) adminRadiosSection.style.display = 'none';
        }
    }

    async function login() {
        const username = document.getElementById('username').value.trim();
        const password = document.getElementById('password').value.trim();

        if (!username || !password) {
            alert('Veuillez saisir un nom d’utilisateur et un mot de passe.');
            return;
        }

        try {
            const response = await fetch('/api/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password })
            });

            if (!response.ok) {
                console.error('Login HTTP error:', response.status);
                alert('Erreur de login (' + response.status + ')');
                return;
            }

            await checkAuth();
        } catch (error) {
            console.error('Erreur connexion:', error);
            alert('Erreur de connexion');
        }
    }

    async function logout() {
        try {
            await fetch('/api/logout', { method: 'POST' });
            await checkAuth();
        } catch (error) {
            console.error('Erreur déconnexion:', error);
        }
    }

    loginBtn.addEventListener('click', login);
    logoutBtn.addEventListener('click', logout);

    // ---------- LECTEUR ----------

    function showPlayer() {
        if (playerContainer) {
            playerContainer.classList.add('active');
        }
    }

    function hidePlayer() {
        if (playerContainer) {
            playerContainer.classList.remove('active');
        }
    }

    function updateCurrentRadioDisplay() {
        if (!currentRadio) {
            currentRadioDisplay.textContent = 'Aucune lecture en cours';
            return;
        }
        // Ne garder que le nom avant la première parenthèse
        const cleanName = currentRadio.name.split('(')[0].trim();
        currentRadioDisplay.textContent = cleanName;
    }

    async function loadStationMeta(radio) {
        if (!nowPlayingCover) return;
        try {
            const res = await fetch('/api/station-meta?url=' + encodeURIComponent(radio.url));
            const data = await res.json();

            nowPlayingCover.innerHTML = '';

            if (data.found && data.favicon) {
                const img = document.createElement('img');
                img.src = data.favicon;
                img.alt = radio.name;
                nowPlayingCover.appendChild(img);
            }
        } catch (err) {
            console.error('Erreur station-meta:', err);
            nowPlayingCover.innerHTML = '';
        }
    }

    function playRadio(radio) {
        currentRadio = radio;
        audioPlayer.src = radio.url;
        audioPlayer.play()
            .then(() => {
                playBtn.disabled = false;
                stopBtn.disabled = false;
                playBtn.textContent = '⏸️';
                updateCurrentRadioDisplay();
                showPlayer();
                loadStationMeta(radio);
            })
            .catch(err => {
                console.error(err);
                alert('Impossible de lire cette station (flux indisponible ou bloqué).');
                hidePlayer();
            });
    }

    function stopPlayback() {
        audioPlayer.pause();
        audioPlayer.currentTime = 0;
        audioPlayer.src = '';
        playBtn.textContent = '▶️';
        currentRadio = null;
        updateCurrentRadioDisplay();
        if (nowPlayingCover) nowPlayingCover.innerHTML = '';
        hidePlayer();
    }

    // Boutons du lecteur
    playBtn.addEventListener('click', () => {
        if (!audioPlayer.src) return;

        if (audioPlayer.paused) {
            audioPlayer.play()
                .then(() => {
                    playBtn.textContent = '⏸️';
                    showPlayer();
                })
                .catch(err => {
                    console.error(err);
                    alert('Impossible de lire le flux.');
                    hidePlayer();
                });
        } else {
            audioPlayer.pause();
            playBtn.textContent = '▶️';
        }
    });

    stopBtn.addEventListener('click', stopPlayback);

    // Volume
    audioPlayer.volume = 0.5;
    volumeControl.value = 50;
    volumeControl.addEventListener('input', e => {
        const v = parseInt(e.target.value, 10) || 0;
        audioPlayer.volume = v / 100;
    });

    audioPlayer.addEventListener('ended', stopPlayback);

    // ---------- RADIOS ----------

    async function loadRadios() {
        try {
            const res = await fetch('/api/radios');
            const radios = await res.json();
            renderRadios(radios);
        } catch (err) {
            console.error(err);
        }
    }

    function renderRadios(radios) {
        radioStationsList.innerHTML = '';

        if (!radios || radios.length === 0) {
            const li = document.createElement('li');
            li.textContent = 'Aucune radio. Ajoutez-en une ci-dessus.';
            radioStationsList.appendChild(li);
            return;
        }

        radios.forEach(radio => {
            const li = document.createElement('li');
            li.className = 'radio-item';

            li.innerHTML = `
                <div class="radio-info">
                    <strong>${radio.name}</strong>
                    ${radio.genre ? `<span class="genre">${radio.genre}</span>` : ''}
                    <div><small>${radio.url}</small></div>
                </div>
                <div class="radio-actions">
                    <button class="play-radio">▶️</button>
                    <button class="delete-btn">🗑️</button>
                </div>
            `;

            li.querySelector('.play-radio').addEventListener('click', () => {
                playRadio(radio);
            });

            li.querySelector('.delete-btn').addEventListener('click', async () => {
                if (!confirm(`Tu veux supprimer cette radio qui est ${radio.name} ?`)) return;
                try {
                    await fetch(`/api/radios/${radio.id}`, { method: 'DELETE' });
                    await loadRadios();
                } catch (err) {
                    console.error(err);
                    alert('Erreur lors de la suppression.');
                }
            });

            radioStationsList.appendChild(li);
        });
    }

    // Ajout de radio AVEC validation + possibilité de forcer

    addRadioBtn.addEventListener('click', async () => {
        const name = radioNameInput.value.trim();
        const url = radioUrlInput.value.trim();
        const genre = radioGenreInput.value.trim();

        if (!name || !url) {
            alert('Nom et URL sont obligatoires.');
            return;
        }

        try {
            const check = await fetch(`/api/validate-stream/${encodeURIComponent(url)}`);
            const checkData = await check.json();
            if (!checkData.valid) {
                const proceed = confirm(
                    "La validation du flux a échoué (URL de flux non valide ou inaccessible depuis le serveur).\n\n" +
                    "Si tu es sûr que l'URL fonctionne dans ton navigateur, tu peux l’ajouter quand même.\n\n" +
                    "Ajouter cette radio malgré tout ?"
                );
                if (!proceed) return;
            }

            const res = await fetch('/api/radios', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name, url, genre })
            });

            if (!res.ok) throw new Error('Erreur API');

            radioNameInput.value = '';
            radioUrlInput.value = '';
            radioGenreInput.value = '';

            await loadRadios();
        } catch (err) {
            console.error(err);
            alert('Erreur lors de l’enregistrement de la radio.');
        }
    });

    // ---------- INIT ----------

    checkAuth();
    loadRadios();
    hidePlayer(); // lecteur caché au début
});