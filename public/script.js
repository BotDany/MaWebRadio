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

    // Éléments d'authentification
    const loginForm = document.getElementById('login-form');
    const adminPanel = document.getElementById('admin-panel');
    const adminUsername = document.getElementById('admin-username');
    const loginBtn = document.getElementById('login-btn');
    const logoutBtn = document.getElementById('logout-btn');

    let currentRadio = null;

    // Vérifier l'état d'authentification au chargement
    checkAuth();

    // Charger les radios depuis l'API
    loadRadios();

    // Volume initial
    audioPlayer.volume = volumeControl.value;
    playBtn.disabled = true;
    stopBtn.disabled = true;

    volumeControl.addEventListener('input', e => {
        audioPlayer.volume = e.target.value;
    });

    playBtn.addEventListener('click', () => {
        if (!audioPlayer.src) return;

        if (audioPlayer.paused) {
            audioPlayer.play()
                .then(() => {
                    playBtn.textContent = '⏸️ Pause';
                })
                .catch(err => {
                    console.error(err);
                    alert('Impossible de lire le flux.');
                });
        } else {
            audioPlayer.pause();
            playBtn.textContent = '▶️ Lecture';
        }
    });

    stopBtn.addEventListener('click', () => {
        audioPlayer.pause();
        audioPlayer.currentTime = 0;
        playBtn.textContent = '▶️ Lecture';
        currentRadio = null;
        updateCurrentRadioDisplay();
    });

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
                alert('URL de flux non valide ou inaccessible.');
                return;
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
                if (!confirm('Supprimer cette radio ?')) return;
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

    function playRadio(radio) {
        currentRadio = radio;
        audioPlayer.src = radio.url;
        audioPlayer.play()
            .then(() => {
                playBtn.disabled = false;
                stopBtn.disabled = false;
                playBtn.textContent = '⏸️ Pause';
                updateCurrentRadioDisplay();
            })
            .catch(err => {
                console.error(err);
                alert('Impossible de lire cette station (HTTP/HTTPS bloqué ou flux indisponible).');
            });
    }

    function updateCurrentRadioDisplay() {
        if (!currentRadio) {
            currentRadioDisplay.innerHTML = '<p>Aucune lecture en cours</p>';
            return;
        }
        currentRadioDisplay.innerHTML = `
            <p><strong>${currentRadio.name}</strong></p>
            <p><small>${currentRadio.url}</small></p>
        `;
    }
});