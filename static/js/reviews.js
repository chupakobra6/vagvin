document.addEventListener('DOMContentLoaded', function () {
    initializeTooltips();
    validateReviewForm();
});

function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

function validateReviewForm() {
    const reviewForm = document.getElementById('review-form');
    if (reviewForm) {
        reviewForm.addEventListener('submit', function (e) {
            const nameInput = document.getElementById('id_name');
            const emailInput = document.getElementById('id_email');
            const ratingInput = document.getElementById('id_rating');
            const textInput = document.getElementById('id_text');
            
            let isValid = true;
            
            if (!nameInput.value || nameInput.value.length < 2) {
                markInvalid(nameInput, 'Имя должно содержать минимум 2 символа.');
                isValid = false;
            } else {
                markValid(nameInput);
            }
            
            if (!emailInput.value || !isValidEmail(emailInput.value)) {
                markInvalid(emailInput, 'Пожалуйста, введите корректный email адрес.');
                isValid = false;
            } else {
                markValid(emailInput);
            }
            
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

function markInvalid(input, message) {
    input.classList.add('is-invalid');
    
    let feedback = input.nextElementSibling;
    if (!feedback || !feedback.classList.contains('invalid-feedback')) {
        feedback = document.createElement('div');
        feedback.className = 'invalid-feedback';
        input.parentNode.insertBefore(feedback, input.nextSibling);
    }
    
    feedback.textContent = message;
}

function markValid(input) {
    input.classList.remove('is-invalid');
    const feedback = input.nextElementSibling;
    if (feedback && feedback.classList.contains('invalid-feedback')) {
        feedback.textContent = '';
    }
}

function isValidEmail(email) {
    const re = /^(([^<>()\[\]\\.,;:\s@"]+(\.[^<>()\[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/;
    return re.test(String(email).toLowerCase());
} 