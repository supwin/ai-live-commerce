// Video Manager JavaScript
// frontend/static/js/video-manager.js

let videos = [];
let currentVideoPath = null;
let displayServerStatus = 'checking';

// Initialize when page loads
document.addEventListener('DOMContentLoaded', function () {
    initializeVideoManager();
});

async function initializeVideoManager() {
    console.log('🎬 Initializing Video Manager...');

    // Check display server status
    await checkDisplayServerStatus();

    // Load video list
    await loadVideoList();

    // Update status every 30 seconds
    setInterval(checkDisplayServerStatus, 30000);

    console.log('✅ Video Manager initialized');
}

// Display Server Functions
async function checkDisplayServerStatus() {
    try {
        const response = await fetch('/api/v1/content-display/status');
        const data = await response.json();

        if (data.success && data.server_running) {
            updateServerStatus('online', `Port ${data.port || 8080}`);
            document.getElementById('connectionCount').textContent = data.active_connections || 0;
        } else {
            updateServerStatus('offline', 'Not running');
            document.getElementById('connectionCount').textContent = '0';
        }
    } catch (error) {
        console.error('Failed to check server status:', error);
        updateServerStatus('offline', 'Error');
    }
}

function updateServerStatus(status, text) {
    const statusElement = document.getElementById('serverStatus');
    statusElement.textContent = text;
    statusElement.className = `status-indicator ${status}`;
    displayServerStatus = status;
}

async function startDisplayServer() {
    try {
        showMessage('Starting display server...', 'info');

        const response = await fetch('/api/v1/content-display/start-server', {
            method: 'POST'
        });

        const data = await response.json();

        if (data.success) {
            showMessage('Display server started successfully!', 'success');
            await checkDisplayServerStatus();

            // Update mobile link
            const mobileLink = document.getElementById('mobileLink');
            mobileLink.href = data.display_pages.mobile;
        } else {
            showMessage(`Failed to start server: ${data.error}`, 'error');
        }
    } catch (error) {
        console.error('Error starting display server:', error);
        showMessage('Error starting display server', 'error');
    }
}

// Video Generation Functions
async function generateVideo() {
    const generateBtn = document.getElementById('generateBtn');
    const statusDiv = document.getElementById('generationStatus');
    const statusText = document.getElementById('statusText');

    try {
        // Get form data
        const productData = {
            name: document.getElementById('productName').value.trim(),
            price: document.getElementById('productPrice').value.trim(),
            description: document.getElementById('productDescription').value.trim()
        };

        const videoStyle = document.getElementById('videoStyle').value;
        const customScript = document.getElementById('customScript').value.trim();

        // Validation
        if (!productData.name) {
            showMessage('Please enter a product name', 'error');
            return;
        }

        // Show loading state
        generateBtn.disabled = true;
        generateBtn.innerHTML = '⏳ Generating...';
        statusDiv.style.display = 'flex';
        statusText.textContent = 'Generating AI script...';

        // Generate video
        const requestData = {
            product_info: productData,
            style: videoStyle,
            custom_script: customScript || undefined
        };

        statusText.textContent = 'Creating video content...';

        const response = await fetch('/api/v1/video-generation/test-generation', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestData)
        });

        const data = await response.json();

        if (data.success) {
            statusText.textContent = 'Video generated successfully!';
            showMessage(`Video generated: ${data.video_filename}`, 'success');

            // Reload video list
            await loadVideoList();

            // Reset form
            document.getElementById('customScript').value = '';

        } else {
            throw new Error(data.error || 'Video generation failed');
        }

    } catch (error) {
        console.error('Video generation error:', error);
        showMessage(`Generation failed: ${error.message}`, 'error');
        statusText.textContent = 'Generation failed';
    } finally {
        // Reset button state
        generateBtn.disabled = false;
        generateBtn.innerHTML = '🎬 Generate Video';

        // Hide status after 3 seconds
        setTimeout(() => {
            statusDiv.style.display = 'none';
        }, 3000);
    }
}

async function generateNewVideo() {
    // Scroll to generation panel
    document.querySelector('.generation-panel').scrollIntoView({
        behavior: 'smooth'
    });

    // Focus on product name
    document.getElementById('productName').focus();
}

// Video List Functions
async function loadVideoList() {
    try {
        const response = await fetch('/api/v1/video-generation/list-videos');
        const data = await response.json();

        if (data.success) {
            videos = data.videos || [];
            renderVideoGrid();
        } else {
            console.error('Failed to load videos:', data.error);
            showMessage('Failed to load video list', 'error');
        }
    } catch (error) {
        console.error('Error loading videos:', error);
        showMessage('Error loading videos', 'error');
    }
}

function renderVideoGrid() {
    const grid = document.getElementById('videoGrid');

    if (videos.length === 0) {
        grid.innerHTML = `
            <div class="loading-placeholder">
                <p>📭 No videos yet</p>
                <p>Generate your first AI video above!</p>
            </div>
        `;
        return;
    }

    grid.innerHTML = videos.map(video => `
        <div class="video-item fade-in" onclick="previewVideo('${video.path}', '${video.filename}')">
            <div class="video-thumbnail">
                🎬
                <!-- TODO: Add video thumbnail preview -->
            </div>
            <div class="video-info">
                <div class="video-title">${video.filename.replace('.mp4', '').replace(/_/g, ' ')}</div>
                <div class="video-meta">
                    <span>📊 ${video.size_mb} MB</span>
                    <span>📅 ${formatDate(video.created)}</span>
                </div>
                <div class="video-actions-grid">
                    <button class="btn btn-primary btn-small" onclick="event.stopPropagation(); playVideoOnDisplay('${video.path}', '${video.filename}')">
                        📺 Play
                    </button>
                    <button class="btn btn-danger btn-small" onclick="event.stopPropagation(); confirmDeleteVideo('${video.filename}')">
                        🗑️ Delete
                    </button>
                </div>
            </div>
        </div>
    `).join('');
}

async function refreshVideoList() {
    showMessage('Refreshing video list...', 'info');
    await loadVideoList();
    showMessage('Video list refreshed', 'success');
}

// Video Preview Functions
function previewVideo(videoPath, filename) {
    currentVideoPath = videoPath;

    const modal = document.getElementById('previewModal');
    const modalTitle = document.getElementById('modalTitle');
    const previewVideo = document.getElementById('previewVideo');

    modalTitle.textContent = filename.replace('.mp4', '').replace(/_/g, ' ');
    previewVideo.src = videoPath;

    modal.style.display = 'flex';

    // Update action buttons
    document.getElementById('playBtn').onclick = () => playOnDisplay();
    document.getElementById('deleteBtn').onclick = () => deleteVideo();
    document.getElementById('downloadBtn').onclick = () => downloadVideo();
}

function closePreview() {
    const modal = document.getElementById('previewModal');
    const previewVideo = document.getElementById('previewVideo');

    modal.style.display = 'none';
    previewVideo.pause();
    previewVideo.src = '';
    currentVideoPath = null;
}

// Video Actions
async function playVideoOnDisplay(videoPath, filename) {
    try {
        if (displayServerStatus !== 'online') {
            showMessage('Display server is not running. Starting server...', 'info');
            await startDisplayServer();
            await new Promise(resolve => setTimeout(resolve, 2000)); // Wait for server
        }

        // Extract filename from path
        const videoFilename = videoPath.split('/').pop();

        const response = await fetch(`/api/v1/video-generation/play-video/${videoFilename}`, {
            method: 'POST'
        });

        const data = await response.json();

        if (data.success) {
            showMessage(`Now playing: ${filename}`, 'success');

            // Show mobile display reminder
            setTimeout(() => {
                showMessage('📱 Video is playing on mobile display: http://localhost:8080/mobile', 'info');
            }, 2000);
        } else {
            showMessage(`Failed to play video: ${data.detail}`, 'error');
        }
    } catch (error) {
        console.error('Error playing video:', error);
        showMessage('Error playing video on display', 'error');
    }
}

async function playOnDisplay() {
    if (currentVideoPath) {
        const filename = currentVideoPath.split('/').pop();
        await playVideoOnDisplay(currentVideoPath, filename);
        closePreview();
    }
}

async function confirmDeleteVideo(filename) {
    if (confirm(`Are you sure you want to delete "${filename}"?`)) {
        await deleteVideoFile(filename);
    }
}

async function deleteVideoFile(filename) {
    try {
        const response = await fetch(`/api/v1/video-generation/delete-video/${filename}`, {
            method: 'DELETE'
        });

        const data = await response.json();

        if (data.success) {
            showMessage(`Video deleted: ${filename}`, 'success');
            await loadVideoList();
        } else {
            showMessage(`Failed to delete video: ${data.detail}`, 'error');
        }
    } catch (error) {
        console.error('Error deleting video:', error);
        showMessage('Error deleting video', 'error');
    }
}

async function deleteVideo() {
    if (currentVideoPath) {
        const filename = currentVideoPath.split('/').pop();
        if (confirm(`Are you sure you want to delete "${filename}"?`)) {
            await deleteVideoFile(filename);
            closePreview();
        }
    }
}

function downloadVideo() {
    if (currentVideoPath) {
        const link = document.createElement('a');
        link.href = currentVideoPath;
        link.download = currentVideoPath.split('/').pop();
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);

        showMessage('Video download started', 'success');
    }
}

// Search and Filter Functions
function filterVideos() {
    const searchTerm = document.getElementById('searchBox').value.toLowerCase();
    const filteredVideos = videos.filter(video =>
        video.filename.toLowerCase().includes(searchTerm)
    );

    // Temporarily replace videos array for rendering
    const originalVideos = videos;
    videos = filteredVideos;
    renderVideoGrid();
    videos = originalVideos;
}

function sortVideos() {
    const sortBy = document.getElementById('sortBy').value;

    videos.sort((a, b) => {
        switch (sortBy) {
            case 'newest':
                return new Date(b.created) - new Date(a.created);
            case 'oldest':
                return new Date(a.created) - new Date(b.created);
            case 'name':
                return a.filename.localeCompare(b.filename);
            case 'size':
                return b.size_mb - a.size_mb;
            default:
                return 0;
        }
    });

    renderVideoGrid();
}

// Utility Functions
function formatDate(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const diffHours = Math.floor((now - date) / (1000 * 60 * 60));

    if (diffHours < 1) {
        return 'Just now';
    } else if (diffHours < 24) {
        return `${diffHours}h ago`;
    } else if (diffHours < 168) { // 7 days
        return `${Math.floor(diffHours / 24)}d ago`;
    } else {
        return date.toLocaleDateString();
    }
}

function showMessage(text, type = 'info') {
    // Remove existing messages
    const existingMessages = document.querySelectorAll('.message');
    existingMessages.forEach(msg => msg.remove());

    // Create new message
    const message = document.createElement('div');
    message.className = `message ${type}`;
    message.textContent = text;

    // Insert after header
    const header = document.querySelector('.header');
    header.insertAdjacentElement('afterend', message);

    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (message.parentNode) {
            message.remove();
        }
    }, 5000);
}

// Keyboard shortcuts
document.addEventListener('keydown', function (event) {
    // Escape to close modal
    if (event.key === 'Escape') {
        closePreview();
    }

    // Ctrl+G to generate new video
    if (event.ctrlKey && event.key === 'g') {
        event.preventDefault();
        generateNewVideo();
    }

    // Ctrl+R to refresh video list
    if (event.ctrlKey && event.key === 'r') {
        event.preventDefault();
        refreshVideoList();
    }
});

// Click outside modal to close
document.getElementById('previewModal').addEventListener('click', function (event) {
    if (event.target === this) {
        closePreview();
    }
});

console.log('🎬 Video Manager JavaScript loaded');