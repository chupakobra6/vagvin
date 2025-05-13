if (typeof window.imageViewerInitialized === 'undefined') {
    window.imageViewerInitialized = false;
}

document.addEventListener('DOMContentLoaded', function() {
    if (window.imageViewerInitialized) {
        console.log('Image viewer already initialized, skipping');
        return;
    }
    
    console.log('Initializing image viewer');
    window.imageViewerInitialized = true;
    
    document.querySelectorAll('.fullscreen-overlay').forEach(el => el.remove());
    
    const overlay = document.createElement('div');
    overlay.className = 'fullscreen-overlay';
    
    const image = document.createElement('img');
    
    const closeBtn = document.createElement('div');
    closeBtn.className = 'close-overlay';
    closeBtn.innerHTML = '&times;';
    
    overlay.appendChild(image);
    overlay.appendChild(closeBtn);
    document.body.appendChild(overlay);
    
    const images = document.querySelectorAll('.fullscreen-img');
    images.forEach(function(img) {
        img.addEventListener('click', function() {
            image.src = this.src;
            overlay.classList.add('active');
        });
    });
    
    closeBtn.addEventListener('click', function() {
        overlay.classList.remove('active');
    });
    
    overlay.addEventListener('click', function(e) {
        if (e.target === overlay) {
            overlay.classList.remove('active');
        }
    });
    
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            overlay.classList.remove('active');
        }
    });
});
