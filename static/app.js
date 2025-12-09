// VIBECODE Frame Grid Viewer

const frameGrid = document.getElementById('frame-grid');
const lightbox = document.getElementById('lightbox');
const lightboxImg = document.getElementById('lightbox-img');
const lightboxFrameNum = document.getElementById('lightbox-frame-num');
const lightboxTimecode = document.getElementById('lightbox-timecode');
const lightboxClose = document.getElementById('lightbox-close');
const lightboxPrev = document.getElementById('lightbox-prev');
const lightboxNext = document.getElementById('lightbox-next');
const movieTitle = document.getElementById('movie-title');

let frames = [];
let currentFrameIndex = 0;

// Load frames from the frames directory
async function loadFrames() {
    try {
        const response = await fetch('/api/frames/');
        const data = await response.json();
        
        if (data.frames && data.frames.length > 0) {
            frames = data.frames;
            if (movieTitle && data.movie_name) {
                movieTitle.textContent = data.movie_name;
            }
            renderGrid();
        } else {
            showEmptyState();
        }
    } catch (error) {
        console.error('Error loading frames:', error);
        showEmptyState();
    }
}

function showEmptyState() {
    frameGrid.innerHTML = `
        <div class="empty-state">
            <p>No frames found.</p>
            <p>Extract frames from a video using:</p>
            <code>python3 extract_frames.py your_video.mp4</code>
        </div>
    `;
}

function renderGrid() {
    frameGrid.innerHTML = '';
    
    frames.forEach((frame, index) => {
        const img = document.createElement('img');
        img.src = frame.thumbnail;
        img.alt = `Frame ${frame.number}`;
        img.dataset.index = index;
        img.loading = 'lazy';
        
        img.addEventListener('click', () => openLightbox(index));
        
        frameGrid.appendChild(img);
    });
}

function openLightbox(index) {
    currentFrameIndex = index;
    updateLightboxImage();
    lightbox.classList.add('active');
    document.body.style.overflow = 'hidden';
}

function closeLightbox() {
    lightbox.classList.remove('active');
    document.body.style.overflow = '';
}

function updateLightboxImage() {
    const frame = frames[currentFrameIndex];
    // Use full-size if available, otherwise thumbnail
    lightboxImg.src = frame.full || frame.thumbnail;
    lightboxFrameNum.textContent = `Frame ${frame.number}`;
    lightboxTimecode.textContent = frame.timecode;
}

function nextFrame() {
    if (currentFrameIndex < frames.length - 1) {
        currentFrameIndex++;
        updateLightboxImage();
    }
}

function prevFrame() {
    if (currentFrameIndex > 0) {
        currentFrameIndex--;
        updateLightboxImage();
    }
}

// Event listeners
lightboxClose.addEventListener('click', closeLightbox);
lightboxNext.addEventListener('click', nextFrame);
lightboxPrev.addEventListener('click', prevFrame);

lightbox.addEventListener('click', (e) => {
    if (e.target === lightbox) {
        closeLightbox();
    }
});

document.addEventListener('keydown', (e) => {
    if (!lightbox.classList.contains('active')) return;
    
    switch (e.key) {
        case 'Escape':
            closeLightbox();
            break;
        case 'ArrowRight':
            nextFrame();
            break;
        case 'ArrowLeft':
            prevFrame();
            break;
    }
});

// Initialize
loadFrames();
