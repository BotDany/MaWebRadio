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
    const radioLogoUrlInput = document.getElementById('radio-logo-url');
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

    function getRadioLogoUrl(radio) {
        if (radio && typeof radio.logo_url === 'string' && radio.logo_url.trim()) {
            return radio.logo_url.trim();
        }
        if (!radio || typeof radio.url !== 'string' || !radio.url.trim()) {
            return '';
        }
        try {
            const u = new URL(radio.url.trim());
            const hostname = u.hostname;
            if (!hostname) return '';
            return 'https://www.google.com/s2/favicons?domain=' + encodeURIComponent(hostname) + '&sz=64';
        } catch (e) {
            return '';
        }
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

        function ensureMarqueeSpan(el) {
            let span = el.querySelector('.marquee');
            if (!span) {
                el.textContent = '';
                span = document.createElement('span');
                span.className = 'marquee';
                el.appendChild(span);
            }
            return span;
        }

        function applyMarqueeIfNeeded(el) {
            const span = ensureMarqueeSpan(el);

            // Reset class before measure
            el.classList.remove('is-scrolling');
            el.style.removeProperty('--marquee-duration');

            // Force layout measurement
            const containerWidth = el.clientWidth;
            const textWidth = span.scrollWidth;

            if (!containerWidth || !textWidth) {
                return;
            }

            const shouldScroll = textWidth > containerWidth + 10;
            if (!shouldScroll) {
                return;
            }

            // Duration based on pixels to travel (tuned for readability)
            const distance = textWidth + containerWidth;
            const pxPerSecond = 55;
            const duration = Math.max(8, Math.min(30, distance / pxPerSecond));
            el.style.setProperty('--marquee-duration', duration.toFixed(2) + 's');

            // Restart animation
            el.classList.add('is-scrolling');
            span.style.animation = 'none';
            // eslint-disable-next-line no-unused-expressions
            span.offsetHeight;
            span.style.animation = '';
        }

        const marqueeSpan = ensureMarqueeSpan(metadataElement);
        if (marqueeSpan.textContent !== displayText) {
            marqueeSpan.textContent = displayText;
            // Apply after DOM update
            requestAnimationFrame(() => applyMarqueeIfNeeded(metadataElement));
        } else {
            // If same text, still ensure scroll state is correct (resize etc.)
            requestAnimationFrame(() => applyMarqueeIfNeeded(metadataElement));
        }

        if (nowPlayingCover) {
            const finalCover = (coverUrl && coverUrl.startsWith('http')) ? coverUrl : '';

            if (finalCover) {
                nowPlayingCover.innerHTML = '';
                const img = document.createElement('img');
                img.src = finalCover;
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
                    <div class="radio-logo"></div>
                    <div class="radio-info-text">
                        <strong>${radio.name}</strong>
                        ${radio.genre ? `<span class="genre">${radio.genre}</span>` : ''}
                        <div><small>${radio.url}</small></div>
                    </div>
                </div>
                <div class="radio-actions">
                    <button class="play-radio">▶️</button>
                    <button class="delete-btn">🗑️</button>
                </div>
            `;

            const logoContainer = li.querySelector('.radio-logo');
            if (logoContainer) {
                logoContainer.innerHTML = '';
                const logoUrl = getRadioLogoUrl(radio);
                if (logoUrl) {
                    const img = document.createElement('img');
                    img.src = logoUrl;
                    img.alt = radio.name;
                    img.loading = 'lazy';
                    img.referrerPolicy = 'no-referrer';
                    img.onerror = () => {
                        try {
                            img.remove();
                        } catch (e) {
                            // ignore
                        }
                    };
                    logoContainer.appendChild(img);
                }
            }

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
        const logo_url = radioLogoUrlInput.value.trim();

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
                body: JSON.stringify({ name, url, genre, logo_url })
            });

            if (!res.ok) throw new Error('Erreur API');

            radioNameInput.value = '';
            radioUrlInput.value = '';
            radioGenreInput.value = '';
            radioLogoUrlInput.value = '';

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