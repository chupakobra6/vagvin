// Global variable to prevent multiple initializations
if (typeof window.imageViewerInitialized === 'undefined') {
    window.imageViewerInitialized = false;
}

document.addEventListener('DOMContentLoaded', function() {
    // Only initialize once
    if (window.imageViewerInitialized) {
        console.log('Image viewer already initialized, skipping');
        return;
    }
    
    console.log('Initializing image viewer');
    window.imageViewerInitialized = true;
    
    // Remove any existing overlays to avoid duplicates
    document.querySelectorAll('.fullscreen-overlay').forEach(el => el.remove());
    
    // Create a simple overlay
    const overlay = document.createElement('div');
    overlay.className = 'fullscreen-overlay';
    
    const image = document.createElement('img');
    
    const closeBtn = document.createElement('div');
    closeBtn.className = 'close-overlay';
    closeBtn.innerHTML = '&times;';
    
    overlay.appendChild(image);
    overlay.appendChild(closeBtn);
    document.body.appendChild(overlay);
    
    // Add click listeners to all fullscreen images
    const images = document.querySelectorAll('.fullscreen-img');
    images.forEach(function(img) {
        img.addEventListener('click', function() {
            image.src = this.src;
            overlay.classList.add('active');
        });
    });
    
    // Close on close button click
    closeBtn.addEventListener('click', function() {
        overlay.classList.remove('active');
    });
    
    // Close when clicking outside the image
    overlay.addEventListener('click', function(e) {
        if (e.target === overlay) {
            overlay.classList.remove('active');
        }
    });
    
    // Close on ESC key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            overlay.classList.remove('active');
        }
    });
});
