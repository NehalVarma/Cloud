// Configuration
const CONFIG = {
    API_BASE_URL: window.location.hostname === 'localhost' 
        ? 'http://localhost:5000' 
        : `http://${window.location.hostname}:5000`,
    LB_API_URL: window.location.hostname === 'localhost' 
        ? 'http://localhost:8080' 
        : `http://${window.location.hostname}:8080`,
    STATS_REFRESH_INTERVAL: 3000, // 3 seconds
    SAMPLE_IMAGES: {
        cat: 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSIjZjBmMGYwIi8+PHRleHQgeD0iNTAlIiB5PSI1MCUiIGZvbnQtc2l6ZT0iNjAiIHRleHQtYW5jaG9yPSJtaWRkbGUiIGR5PSIuM2VtIj7wn5CxPC90ZXh0Pjwvc3ZnPg==',
        dog: 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSIjZjBmMGYwIi8+PHRleHQgeD0iNTAlIiB5PSI1MCUiIGZvbnQtc2l6ZT0iNjAiIHRleHQtYW5jaG9yPSJtaWRkbGUiIGR5PSIuM2VtIj7wn5C2PC90ZXh0Pjwvc3ZnPg==',
        car: 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSIjZjBmMGYwIi8+PHRleHQgeD0iNTAlIiB5PSI1MCUiIGZvbnQtc2l6ZT0iNjAiIHRleHQtYW5jaG9yPSJtaWRkbGUiIGR5PSIuM2VtIj7wn5qXPC90ZXh0Pjwvc3ZnPg==',
        flower: 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSIjZjBmMGYwIi8+PHRleHQgeD0iNTAlIiB5PSI1MCUiIGZvbnQtc2l6ZT0iNjAiIHRleHQtYW5jaG9yPSJtaWRkbGUiIGR5PSIuM2VtIj7wn42YPC90ZXh0Pjwvc3ZnPg==',
        food: 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSIjZjBmMGYwIi8+PHRleHQgeD0iNTAlIiB5PSI1MCUiIGZvbnQtc2l6ZT0iNjAiIHRleHQtYW5jaG9yPSJtaWRkbGUiIGR5PSIuM2VtIj7wn42VPC90ZXh0Pjwvc3ZnPg=='
    }
};

// Global state
let currentImageFile = null;
let lastResult = null;
let statsInterval = null;

// DOM elements
const dropZone = document.getElementById('drop-zone');
const fileInput = document.getElementById('file-input');
const fileSelectBtn = document.getElementById('file-select-btn');
const imagePreview = document.getElementById('image-preview');
const previewImg = document.getElementById('preview-img');
const classifyBtn = document.getElementById('classify-btn');
const clearBtn = document.getElementById('clear-btn');
const loading = document.getElementById('loading');
const resultsSection = document.getElementById('results-section');
const themeToggle = document.getElementById('theme-toggle');
const errorPanel = document.getElementById('error-panel');
const errorMessage = document.getElementById('error-message');
const errorClose = document.getElementById('error-close');

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    initializeEventListeners();
    initializeTheme();
    startStatsRefresh();
    checkServerHealth();
});

function initializeEventListeners() {
    // File upload handlers
    dropZone.addEventListener('click', () => fileInput.click());
    dropZone.addEventListener('dragover', handleDragOver);
    dropZone.addEventListener('drop', handleDrop);
    dropZone.addEventListener('dragleave', handleDragLeave);
    
    fileInput.addEventListener('change', handleFileSelect);
    fileSelectBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        fileInput.click();
    });
    
    // Action buttons
    classifyBtn.addEventListener('click', classifyImage);
    clearBtn.addEventListener('click', clearImage);
    document.getElementById('repeat-btn').addEventListener('click', classifyImage);
    document.getElementById('copy-json-btn').addEventListener('click', copyResultJSON);
    
    // Theme toggle
    themeToggle.addEventListener('click', toggleTheme);
    
    // Error panel
    errorClose.addEventListener('click', hideError);
    
    // Gallery items
    document.querySelectorAll('.gallery-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const imageType = e.target.closest('.gallery-item').dataset.image;
            loadSampleImage(imageType);
        });
    });
}

function initializeTheme() {
    const savedTheme = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-theme', savedTheme);
}

function toggleTheme() {
    const currentTheme = document.documentElement.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
}

// File handling
function handleDragOver(e) {
    e.preventDefault();
    dropZone.classList.add('dragover');
}

function handleDragLeave(e) {
    e.preventDefault();
    dropZone.classList.remove('dragover');
}

function handleDrop(e) {
    e.preventDefault();
    dropZone.classList.remove('dragover');
    
    const files = e.dataTransfer.files;
    if (files.length > 0) {
        handleFile(files[0]);
    }
}

function handleFileSelect(e) {
    const file = e.target.files[0];
    if (file) {
        handleFile(file);
    }
}

function handleFile(file) {
    // Validate file type
    if (!file.type.startsWith('image/')) {
        showError('Please select a valid image file');
        return;
    }
    
    // Validate file size (10MB limit)
    if (file.size > 10 * 1024 * 1024) {
        showError('File size must be less than 10MB');
        return;
    }
    
    currentImageFile = file;
    
    // Show preview
    const reader = new FileReader();
    reader.onload = function(e) {
        previewImg.src = e.target.result;
        previewImg.alt = `Preview of ${file.name}`;
        dropZone.style.display = 'none';
        imagePreview.style.display = 'block';
    };
    reader.readAsDataURL(file);
}

function loadSampleImage(imageType) {
    const imageData = CONFIG.SAMPLE_IMAGES[imageType];
    if (!imageData) return;
    
    // Convert data URL to blob
    fetch(imageData)
        .then(res => res.blob())
        .then(blob => {
            const file = new File([blob], `sample-${imageType}.svg`, { type: 'image/svg+xml' });
            handleFile(file);
        })
        .catch(err => {
            showError('Failed to load sample image');
        });
}

function clearImage() {
    currentImageFile = null;
    dropZone.style.display = 'block';
    imagePreview.style.display = 'none';
    resultsSection.style.display = 'none';
    fileInput.value = '';
}

// Classification
async function classifyImage() {
    if (!currentImageFile) {
        showError('Please select an image first');
        return;
    }
    
    // Show loading state
    loading.style.display = 'block';
    resultsSection.style.display = 'none';
    classifyBtn.disabled = true;
    
    try {
        const formData = new FormData();
        formData.append('image', currentImageFile);
        
        const response = await fetch(`${CONFIG.API_BASE_URL}/predict`, {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const result = await response.json();
        lastResult = result;
        
        if (result.error) {
            throw new Error(result.error);
        }
        
        displayResult(result);
        
    } catch (error) {
        console.error('Classification error:', error);
        showError(`Classification failed: ${error.message}`);
    } finally {
        loading.style.display = 'none';
        classifyBtn.disabled = false;
    }
}

function displayResult(result) {
    // Update result elements
    document.getElementById('result-label').textContent = result.label || 'Unknown';
    
    const confidence = (result.confidence * 100).toFixed(1);
    document.getElementById('confidence-text').textContent = `${confidence}%`;
    document.getElementById('confidence-fill').style.width = `${confidence}%`;
    
    document.getElementById('server-id').textContent = result.server_id || 'Unknown';
    document.getElementById('model-version').textContent = result.model_version || 'v1';
    document.getElementById('latency').textContent = `${result.latency_ms || 0}ms`;
    
    // Show results section
    resultsSection.style.display = 'block';
    resultsSection.scrollIntoView({ behavior: 'smooth' });
}

function copyResultJSON() {
    if (!lastResult) return;
    
    const jsonString = JSON.stringify(lastResult, null, 2);
    navigator.clipboard.writeText(jsonString).then(() => {
        // Visual feedback
        const btn = document.getElementById('copy-json-btn');
        const originalText = btn.textContent;
        btn.textContent = '✅ Copied!';
        setTimeout(() => {
            btn.textContent = originalText;
        }, 2000);
    }).catch(err => {
        showError('Failed to copy to clipboard');
    });
}

// Server statistics
function startStatsRefresh() {
    refreshStats();
    statsInterval = setInterval(refreshStats, CONFIG.STATS_REFRESH_INTERVAL);
}

async function refreshStats() {
    try {
        const response = await fetch(`${CONFIG.LB_API_URL}/api/server-stats`);
        if (!response.ok) {
            throw new Error('Failed to fetch stats');
        }
        
        const data = await response.json();
        updateStatsDisplay(data);
        
    } catch (error) {
        console.warn('Stats refresh failed:', error);
        updateStatsDisplay({ 
            algorithm: 'unknown', 
            servers: [], 
            total_requests: 0 
        });
    }
}

function updateStatsDisplay(data) {
    // Update header info
    document.getElementById('current-algorithm').textContent = data.algorithm || 'unknown';
    document.getElementById('total-requests').textContent = data.total_requests || 0;
    
    // Update server stats
    const statsContainer = document.getElementById('server-stats');
    
    if (!data.servers || data.servers.length === 0) {
        statsContainer.innerHTML = '<div class="stats-loading">No server data available</div>';
        return;
    }
    
    const maxRequests = Math.max(...data.servers.map(s => s.request_count || 0), 1);
    
    statsContainer.innerHTML = data.servers.map(server => `
        <div class="server-row">
            <div class="server-id">${server.server_id}</div>
            <div class="server-health">
                <div class="health-dot ${server.healthy ? 'healthy' : 'unhealthy'}"></div>
                <span>${server.healthy ? 'Healthy' : 'Unhealthy'}</span>
            </div>
            <div class="request-bar">
                <div class="bar-visual">
                    <div class="bar-fill" style="width: ${(server.request_count / maxRequests) * 100}%"></div>
                </div>
                <div class="bar-text">${server.request_count || 0}</div>
            </div>
            <div class="latency-info">${server.latency_ms || 0}ms</div>
            <div class="cpu-info">${server.cpu_percent || 0}% CPU</div>
        </div>
    `).join('');
}

// Server health check
async function checkServerHealth() {
    const statusDot = document.querySelector('.status-dot');
    const statusText = document.querySelector('.status-text');
    
    try {
        const response = await fetch(`${CONFIG.API_BASE_URL}/health`, { timeout: 5000 });
        
        if (response.ok) {
            statusDot.className = 'status-dot healthy';
            statusText.textContent = 'Service Online';
        } else {
            statusDot.className = 'status-dot unhealthy';
            statusText.textContent = 'Service Issues';
        }
    } catch (error) {
        statusDot.className = 'status-dot unhealthy';
        statusText.textContent = 'Service Offline';
    }
    
    // Check again in 30 seconds
    setTimeout(checkServerHealth, 30000);
}

// Error handling
function showError(message) {
    errorMessage.textContent = message;
    errorPanel.style.display = 'block';
    
    // Auto-hide after 5 seconds
    setTimeout(hideError, 5000);
}

function hideError() {
    errorPanel.style.display = 'none';
}

// Cleanup on page unload
window.addEventListener('beforeunload', function() {
    if (statsInterval) {
        clearInterval(statsInterval);
    }
});