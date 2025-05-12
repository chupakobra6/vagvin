document.addEventListener('DOMContentLoaded', function () {
    initializeTooltips();
    validateReviewForm();
});

/**
 * Initialize tooltips
 */
function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

/**
 * Validate review form submission
 */
function validateReviewForm() {
    const reviewForm = document.getElementById('review-form');
    if (reviewForm) {
        reviewForm.addEventListener('submit', function (e) {
            const nameInput = document.getElementById('id_name');
            const emailInput = document.getElementById('id_email');
            const ratingInput = document.getElementById('id_rating');
            const textInput = document.getElementById('id_text');
            
            let isValid = true;
            
            // Validate name
            if (!nameInput.value || nameInput.value.length < 2) {
                markInvalid(nameInput, 'Имя должно содержать минимум 2 символа.');
                isValid = false;
            } else {
                markValid(nameInput);
            }
            
            // Validate email
            if (!emailInput.value || !isValidEmail(emailInput.value)) {
                markInvalid(emailInput, 'Пожалуйста, введите корректный email адрес.');
                isValid = false;
            } else {
                markValid(emailInput);
            }
            
            // Validate text
            if (!textInput.value || textInput.value.length < 10) {
                markInvalid(textInput, 'Текст отзыва должен содержать минимум 10 символов.');
                isValid = false;
            } else if (textInput.value.length > 1000) {
                markInvalid(textInput, 'Текст отзыва не должен превышать 1000 символов.');
                isValid = false;
            } else {
                markValid(textInput);
            }
            
            if (!isValid) {
                e.preventDefault();
            }
        });
    }
}

/**
 * Mark form field as invalid with error message
 */
function markInvalid(input, message) {
    input.classList.add('is-invalid');
    
    // Find the existing feedback element or create a new one
    let feedback = input.nextElementSibling;
    if (!feedback || !feedback.classList.contains('invalid-feedback')) {
        feedback = document.createElement('div');
        feedback.className = 'invalid-feedback';
        input.parentNode.insertBefore(feedback, input.nextSibling);
    }
    
    feedback.textContent = message;
}

/**
 * Mark form field as valid
 */
function markValid(input) {
    input.classList.remove('is-invalid');
    const feedback = input.nextElementSibling;
    if (feedback && feedback.classList.contains('invalid-feedback')) {
        feedback.textContent = '';
    }
}

/**
 * Validate email format
 */
function isValidEmail(email) {
    const re = /^(([^<>()\[\]\\.,;:\s@"]+(\.[^<>()\[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/;
    return re.test(String(email).toLowerCase());
} 