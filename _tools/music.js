/*
 * music.js - Continuous background music player
 * Uses localStorage to remember track & time across page transitions.
 */

// ADD YOUR SONG URLS/PATHS HERE
const playlist = [
    'audio/comfy-in-nautica.mp3',
    'audio/instrumental.mp3',
    'audio/hypertension.mp3',
    'audio/delete.mp3',
    'audio/dancing-without-moving.mp3',
    'audio/cs60.mp3',
    'audio/since-i-left-you.mp3',
    'audio/15 Can\'t Make A Sound.mp3'
];

(function initMusicPlayer() {
    // If no songs, we just exit early
    if (playlist.length === 0) {
        console.log("No songs in playlist. Add songs to _tools/music.js to play background music.");
        return;
    }

    const base = window.nublogBase || '.';

    let audio = new Audio();
    audio.id = 'bg-music';
    audio.volume = 0.5;

    let userInteracted = false;
    let savedIndex = parseInt(localStorage.getItem('musicIndex'));
    let savedTime = parseFloat(localStorage.getItem('musicTime'));
    let wasPlaying = localStorage.getItem('musicPlaying') === 'true';

    // Check if we are on the splash/boot page - if so we don't build the player UI
    const isSplashPage = window.location.pathname.endsWith('/') || window.location.pathname.endsWith('index.html');

    if (isSplashPage) {
        // Do not build player on splash screen
        return;
    }

    // Read saved state
    if (isNaN(savedIndex) || savedIndex >= playlist.length) {
        savedIndex = Math.floor(Math.random() * playlist.length);
        localStorage.setItem('musicIndex', savedIndex);
    }

    // Resolve path relative to the current site root
    let currentTrack = playlist[savedIndex];
    if (!currentTrack.startsWith('http')) {
        currentTrack = `${base}/${currentTrack}`;
    }

    audio.src = currentTrack;
    audio.currentTime = savedTime || 0; // Ensure savedTime is not NaN

    // Save current time frequently
    audio.addEventListener('timeupdate', () => {
        if (!audio.paused) {
            localStorage.setItem('musicTime', audio.currentTime);
        }
    });

    function playRandomTrack() {
        let newIndex = savedIndex;
        if (playlist.length > 1) {
            while (newIndex === savedIndex) {
                newIndex = Math.floor(Math.random() * playlist.length);
            }
        }
        savedIndex = newIndex;
        localStorage.setItem('musicIndex', savedIndex);
        localStorage.setItem('musicTime', 0);

        let nextTrack = playlist[savedIndex];
        if (!nextTrack.startsWith('http')) {
            nextTrack = `${base}/${nextTrack}`;
        }
        audio.src = nextTrack;
        audio.play().then(() => {
            if (window.updateUI) window.updateUI(true);
        }).catch(console.error);
    }

    // When a song ends, play the next one randomly
    audio.addEventListener('ended', playRandomTrack);

    function attemptAutoplay() {
        if (sessionStorage.getItem('musicPlaying') === 'true' || wasPlaying) {
            audio.play().then(() => {
                userInteracted = true;
                localStorage.setItem('musicPlaying', 'true');
                if (window.updateUI) window.updateUI(true);
            }).catch((err) => {
                console.log("Autoplay prevented, waiting for interaction:", err);
                // We DO NOT set 'musicPlaying' to false here! 
                // We must remember the user's intent so it tries again on the next page if needed.
                if (window.updateUI) window.updateUI(false);

                // Add a one-time listener for any organic interaction to jumpstart the audio
                const startOnAnyInteraction = () => {
                    audio.play().then(() => {
                        localStorage.setItem('musicPlaying', 'true');
                        if (window.updateUI) window.updateUI(true);

                        // Cleanup
                        document.removeEventListener('click', startOnAnyInteraction);
                        document.removeEventListener('keydown', startOnAnyInteraction);
                        document.removeEventListener('touchstart', startOnAnyInteraction);
                    }).catch(e => console.log(e));
                };

                document.addEventListener('click', startOnAnyInteraction);
                document.addEventListener('keydown', startOnAnyInteraction);
                document.addEventListener('touchstart', startOnAnyInteraction);
            });
            // Clear the one-time boot flag
            sessionStorage.removeItem('musicPlaying');
        }
    }

    // Attempt autoplay immediately or after interaction
    attemptAutoplay();

    // Determine where to inject the UI, preferably once DOM is loaded
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => buildUI(audio, playRandomTrack));
    } else {
        buildUI(audio, playRandomTrack);
    }
})();

function buildUI(audio, playNextCallback) {
    if (document.getElementById('music-player-ui')) return;

    const container = document.createElement('div');
    container.id = 'music-player-ui';
    container.style.cssText = `
        position: fixed;
        bottom: 10px;
        right: 10px;
        background: #111;
        color: #33CCAA;
        border: 1px solid #444;
        padding: 5px 10px;
        font-family: monospace;
        font-size: 12px;
        z-index: 1000;
        display: flex;
        align-items: center;
        gap: 10px;
        opacity: 0.8;
    `;

    container.onmouseenter = () => container.style.opacity = '1';
    container.onmouseleave = () => container.style.opacity = '0.8';

    const playBtn = document.createElement('button');
    playBtn.innerText = audio.paused ? '▶' : '⏸';
    playBtn.style.cssText = `
        background: none;
        color: inherit;
        border: 1px solid #33CCAA;
        cursor: pointer;
        font-family: monospace;
        padding: 2px 5px;
    `;

    const label = document.createElement('span');
    label.innerText = 'bgm';

    window.updateUI = (playing) => {
        playBtn.innerText = playing ? '⏸' : '▶';
    };

    playBtn.onclick = () => {
        if (audio.paused) {
            audio.play().then(() => {
                localStorage.setItem('musicPlaying', 'true');
                updateUI(true);
            });
        } else {
            audio.pause();
            localStorage.setItem('musicPlaying', 'false');
            updateUI(false);
        }
    };

    const nextBtn = document.createElement('button');
    nextBtn.innerText = '⏭';
    nextBtn.style.cssText = playBtn.style.cssText;

    nextBtn.onclick = () => {
        localStorage.setItem('musicPlaying', 'true');
        if (typeof playNextCallback === 'function') {
            playNextCallback();
        }
    };

    container.appendChild(label);
    container.appendChild(playBtn);
    if (playlist.length > 1) {
        container.appendChild(nextBtn);
    }

    document.body.appendChild(container);
}
