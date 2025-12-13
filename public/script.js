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
    let nowPlayingInterval = null;

    // ---------- UTILS ----------

    function getProxyUrl(url) {
        if (url.startsWith('http://')) {
            return '/proxy-stream/' + url.replace('http://', '');
        }
        return url;
    }

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

    async function fetchNowPlayingFromApi() {
        if (!currentRadio || !currentRadio.name || !currentRadio.url) return;
        try {
            const params = new URLSearchParams({
                name: currentRadio.name,
                url: currentRadio.url
            });
            const res = await fetch('/api/now-playing?' + params.toString());
            if (!res.ok) return;
            const data = await res.json();
            if (!data) return;
            updateMetadataFromApi(data);
        } catch (e) {
            // ignore
        }
    }

    function updateNowPlayingMetadata() {
        if (!currentRadio || !audioPlayer.src) return;
        if (nowPlayingInterval) {
            clearInterval(nowPlayingInterval);
            nowPlayingInterval = null;
        }
        fetchNowPlayingFromApi();
        nowPlayingInterval = setInterval(fetchNowPlayingFromApi, 25000);
    }

    function updateMetadataFromApi(payload) {
        const title = (payload.title || '').toString().trim();
        const artist = (payload.artist || '').toString().trim();
        const coverUrl = (payload.cover_url || '').toString().trim();

        let displayText = '';
        if (artist && title) displayText = artist + ' - ' + title;
        else if (title) displayText = title;
        else displayText = 'Aucune information de lecture disponible';

        let metadataElement = document.getElementById('now-playing-metadata');
        if (!metadataElement) {
            metadataElement = document.createElement('div');
            metadataElement.id = 'now-playing-metadata';
            metadataElement.className = 'now-playing-metadata';
            const parent = currentRadioDisplay.parentNode;
            parent.insertBefore(metadataElement, currentRadioDisplay.nextSibling);
        }

        if (metadataElement.textContent !== displayText) {
            metadataElement.textContent = displayText;
        }

        if (nowPlayingCover) {
            if (coverUrl && coverUrl.startsWith('http')) {
                nowPlayingCover.innerHTML = '';
                const img = document.createElement('img');
                img.src = coverUrl;
                img.alt = currentRadio ? currentRadio.name : 'cover';
                nowPlayingCover.appendChild(img);
            }
        }

        if (currentRadio && 'mediaSession' in navigator) {
            try {
                navigator.mediaSession.metadata = new MediaMetadata({
                    title: title || displayText,
                    artist: artist || (currentRadio ? currentRadio.name : ''),
                    album: 'En écoute',
                    artwork: coverUrl && coverUrl.startsWith('http') ? [
                        { src: coverUrl, sizes: '512x512', type: 'image/jpeg' },
                        { src: coverUrl, sizes: '192x192', type: 'image/jpeg' },
                        { src: coverUrl, sizes: '96x96', type: 'image/jpeg' }
                    ] : []
                });
            } catch (e) {
                // ignore
            }
        }
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
                updateNowPlayingMetadata();
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
        const metadataElement = document.getElementById('now-playing-metadata');
        if (metadataElement) metadataElement.remove();
        if (nowPlayingInterval) {
            clearInterval(nowPlayingInterval);
            nowPlayingInterval = null;
        }
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
    
    // Mise à jour du volume quand le slider est déplacé
    volumeControl.addEventListener('input', e => {
        const v = parseInt(e.target.value, 10) || 0;
        audioPlayer.volume = v / 100;
    });
    
    // Bouton pour baisser le volume
    document.getElementById('volume-down').addEventListener('click', () => {
        let newVolume = Math.max(0, audioPlayer.volume - 0.1); // Diminue de 10%
        audioPlayer.volume = newVolume;
        volumeControl.value = Math.round(newVolume * 100);
    });
    
    // Bouton pour augmenter le volume
    document.getElementById('volume-up').addEventListener('click', () => {
        let newVolume = Math.min(1, audioPlayer.volume + 0.1); // Augmente de 10%
        audioPlayer.volume = newVolume;
        volumeControl.value = Math.round(newVolume * 100);
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

    // ---------- OPENRADIO DISCOVER ----------
    
    // Variables pour la découverte OpenRadio
    const searchQuery = document.getElementById('search-query');
    const countryFilter = document.getElementById('country-filter');
    const genreFilter = document.getElementById('genre-filter');
    const searchRadiosBtn = document.getElementById('search-radios');
    const discoverResults = document.getElementById('discover-results');

    // Charger les filtres
    async function loadDiscoverFilters() {
        try {
            // Charger les pays
            const countriesRes = await fetch('/api/openradio/countries');
            const countriesData = await countriesRes.json();
            if (countriesData.countries) {
                countriesData.countries.forEach(country => {
                    const option = document.createElement('option');
                    option.value = country.code;
                    option.textContent = country.name;
                    countryFilter.appendChild(option);
                });
            }

            // Charger les genres
            const genresRes = await fetch('/api/openradio/genres');
            const genresData = await genresRes.json();
            if (genresData.genres) {
                genresData.genres.forEach(genre => {
                    const option = document.createElement('option');
                    option.value = genre;
                    option.textContent = genre;
                    genreFilter.appendChild(option);
                });
            }
        } catch (error) {
            console.error('Erreur chargement filtres:', error);
        }
    }

    // Rechercher des radios
    async function searchRadios() {
        const query = searchQuery.value.trim();
        const country = countryFilter.value;
        const genre = genreFilter.value;

        if (!query && !country && !genre) {
            alert('Veuillez entrer une recherche ou sélectionner un filtre');
            return;
        }

        try {
            const params = new URLSearchParams();
            if (query) params.append('query', query);
            if (country) params.append('country', country);
            if (genre) params.append('genre', genre);
            params.append('limit', '20');

            const response = await fetch(`/api/openradio/search?${params}`);
            const data = await response.json();
            renderDiscoverResults(data.stations || []);
        } catch (error) {
            console.error('Erreur recherche radios:', error);
            discoverResults.innerHTML = '<p>Erreur lors de la recherche</p>';
        }
    }

    // Afficher les résultats
    function renderDiscoverResults(stations) {
        discoverResults.innerHTML = '';

        if (!stations || stations.length === 0) {
            discoverResults.innerHTML = '<p>Aucune radio trouvée</p>';
            return;
        }

        stations.forEach(station => {
            const div = document.createElement('div');
            div.className = 'discover-radio-item';

            div.innerHTML = `
                <div class="discover-radio-header">
                    <span class="discover-radio-name">${station.name}</span>
                    <span class="discover-radio-country">${station.country}</span>
                </div>
                <div class="discover-radio-details">
                    <span class="discover-radio-genre">${station.genre || 'Non spécifié'}</span>
                </div>
                <div class="discover-radio-actions">
                    <button class="play-radio-btn" data-name="${station.name}" data-url="${station.url}">
                        Écouter
                    </button>
                    <button class="add-radio-btn" data-name="${station.name}" data-url="${station.url}" data-genre="${station.genre || ''}">
                        Ajouter
                    </button>
                </div>
            `;

            discoverResults.appendChild(div);
        });

        // Ajouter les écouteurs d'événements
        document.querySelectorAll('.play-radio-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const radio = {
                    name: e.target.getAttribute('data-name'),
                    url: e.target.getAttribute('data-url')
                };
                playRadio(radio);
            });
        });

        document.querySelectorAll('.add-radio-btn').forEach(btn => {
            btn.addEventListener('click', async (e) => {
                const radio = {
                    name: e.target.getAttribute('data-name'),
                    url: e.target.getAttribute('data-url'),
                    genre: e.target.getAttribute('data-genre')
                };
                
                try {
                    const response = await fetch('/api/radios', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify(radio)
                    });

                    if (response.ok) {
                        alert('Radio ajoutée avec succès !');
                        loadRadios(); // Recharger la liste des radios
                    } else {
                        throw new Error('Erreur lors de l\'ajout');
                    }
                } catch (error) {
                    console.error('Erreur:', error);
                    alert('Erreur lors de l\'ajout de la radio');
                }
            });
        });
    }

    // Initialisation OpenRadio
    if (searchRadiosBtn) {
        searchRadiosBtn.addEventListener('click', searchRadios);
        loadDiscoverFilters();
        
        // Permettre la recherche avec Entrée
        searchQuery.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                searchRadios();
            }
        });
    }

    // ---------- INIT ----------

    checkAuth();
    loadRadios();
    hidePlayer(); // lecteur caché au début
});