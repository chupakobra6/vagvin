document.addEventListener('DOMContentLoaded', function () {
    // Create overlay once
    const overlay = document.createElement('div');
    overlay.className = 'fullscreen-overlay';

    const closeBtn = document.createElement('div');
    closeBtn.className = 'close-overlay';
    closeBtn.innerHTML = '&times;';
    closeBtn.addEventListener('click', function () {
        overlay.classList.remove('active');
    });

    const fullscreenImg = document.createElement('img');
    overlay.appendChild(fullscreenImg);
    overlay.appendChild(closeBtn);
    document.body.appendChild(overlay);

    // Close when clicking on overlay
    overlay.addEventListener('click', function (e) {
        if (e.target === overlay) {
            overlay.classList.remove('active');
        }
    });

    // Handle clicks on all images
    const images = document.querySelectorAll('.fullscreen-img');
    images.forEach(function (img) {
        img.addEventListener('click', function () {
            fullscreenImg.src = this.src;
            overlay.classList.add('active');
        });
    });

    // Close on ESC key
    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape') {
            overlay.classList.remove('active');
        }
    });
});
