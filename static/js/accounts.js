document.addEventListener('DOMContentLoaded', function () {
    initializeTooltips();
    initializeReferralCopy();
    initializeEmailManagement();
    initializePaymentForms();
    checkPaymentInitiated();
    loadUserQueries();

    const formElements = document.querySelectorAll('form input:not([type="password"]), form select, form textarea');
    
    formElements.forEach(element => {
        element.addEventListener('blur', function() {
            if (this.value.trim() !== '') {
                this.classList.add('is-valid');
            } else if (this.required) {
                this.classList.add('is-invalid');
            }
        });
        
        element.addEventListener('focus', function() {
            this.classList.remove('is-invalid');
            this.classList.remove('is-valid');
        });
    });

    const passwordToggles = document.querySelectorAll('.password-toggle');
    
    passwordToggles.forEach(toggle => {
        toggle.addEventListener('click', function() {
            const passwordField = document.querySelector(this.dataset.target);
            
            if (passwordField.type === 'password') {
                passwordField.type = 'text';
                this.innerHTML = '<i class="fas fa-eye-slash"></i>';
            } else {
                passwordField.type = 'password';
                this.innerHTML = '<i class="fas fa-eye"></i>';
            }
        });
    });
});

function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

function initializeReferralCopy() {
    const copyButton = document.querySelector('.btn-copy-referral');
    if (copyButton) {
        copyButton.addEventListener('click', function () {
            const referralLink = this.dataset.referralLink;
            navigator.clipboard.writeText(referralLink);
            const originalIcon = this.innerHTML;
            this.innerHTML = '<i class="fas fa-check text-success"></i>';
            setTimeout(() => {
                this.innerHTML = originalIcon;
            }, 1000);
        });
    }
}

function initializeEmailManagement() {
    initializeAddEmail();
    initializeRemoveEmail();
}

function initializeAddEmail() {
    const addEmailForm = document.getElementById('add-email-form');
    if (addEmailForm) {
        addEmailForm.addEventListener('submit', function (e) {
            e.preventDefault();
            const emailInput = document.getElementById('id_email');
            const formData = new FormData();
            formData.append('email', emailInput.value);
            
            fetch(addEmailForm.dataset.url, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': getCsrfToken()
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    location.reload();
                } else {
                    console.error('Error:', data.message || 'Произошла ошибка');
                    showAlert(data.message || 'Произошла ошибка', 'danger');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showAlert('Произошла ошибка при отправке запроса', 'danger');
            });
        });
    }
}

function initializeRemoveEmail() {
    const removeEmailButtons = document.querySelectorAll('.remove-email');
    removeEmailButtons.forEach(button => {
        button.addEventListener('click', function () {
            const email = this.dataset.email;
            const formData = new FormData();
            formData.append('email', email);
            
            fetch(this.dataset.url, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': getCsrfToken()
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    location.reload();
                } else {
                    console.error('Error:', data.message || 'Произошла ошибка');
                    showAlert(data.message || 'Произошла ошибка', 'danger');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showAlert('Произошла ошибка при отправке запроса', 'danger');
            });
        });
    });
}

function initializePaymentForms() {
    const amountButtons = document.querySelectorAll('.amount-btn');
    amountButtons.forEach(button => {
        button.addEventListener('click', function() {
            const targetId = this.dataset.target;
            const amount = this.dataset.amount;
            const inputField = document.getElementById(targetId);
            
            if (inputField) {
                inputField.value = amount;
            }

            const parentForm = this.closest('form');
            if (parentForm) {
                parentForm.querySelectorAll('.amount-btn').forEach(btn => {
                    btn.classList.remove('active', 'btn-primary');
                    btn.classList.add('btn-outline-primary');
                });
                this.classList.remove('btn-outline-primary');
                this.classList.add('btn-primary', 'active');
            }
        });
    });
    
    // Set up payment forms
    initializePaymentSubmit('robokassa-form');
    initializePaymentSubmit('yookassa-form');
    initializePaymentSubmit('heleket-form');
}

function initializePaymentSubmit(formId) {
    const form = document.getElementById(formId);
    if (form) {
        form.addEventListener('submit', function (e) {
            e.preventDefault();
            const amountInput = form.querySelector('input[type="number"]');
            if (!amountInput.value || parseFloat(amountInput.value) <= 0) {
                showAlert('Пожалуйста, введите корректную сумму пополнения', 'warning');
                return;
            }
            
            const amount = parseFloat(amountInput.value);
            
            let commissionRate = 0.1;
            if (form.id === 'heleket-form') {
                commissionRate = 0.06;
            }
            const totalAmount = amount * (1 + commissionRate);
            
            const submitBtn = form.querySelector('button[type="submit"]');
            const originalBtnText = submitBtn.innerHTML;
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Загрузка...';
            
            fetch(form.dataset.url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCsrfToken()
                },
                body: JSON.stringify({
                    amount: amount,
                    total_amount: totalAmount
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.payment_url) {
                    window.open(data.payment_url, '_blank');
                    sessionStorage.setItem('payment_initiated', '1');
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = originalBtnText;
                } else {
                    showAlert(data.error || 'Произошла ошибка при создании платежа', 'danger');
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = originalBtnText;
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showAlert('Произошла ошибка при создании платежа', 'danger');
                submitBtn.disabled = false;
                submitBtn.innerHTML = originalBtnText;
            });
        });
    }
}

function checkPaymentInitiated() {
    if (sessionStorage.getItem('payment_initiated')) {
        sessionStorage.removeItem('payment_initiated');
        window.location.reload();
    }
}

function showAlert(message, type) {
    const alertsContainer = document.getElementById('alerts-container');
    if (!alertsContainer) return;
    
    const alert = document.createElement('div');
    alert.className = `alert alert-${type} alert-dismissible fade show`;
    alert.role = 'alert';
    alert.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    alertsContainer.appendChild(alert);
}

function getCsrfToken() {
    return document.querySelector('[name=csrfmiddlewaretoken]').value;
}

function loadUserQueries() {
    const queriesTable = document.getElementById('queries-table');
    if (!queriesTable) return;

    fetch(queriesTable.dataset.url)
        .then(response => {
            if (!response.ok) {
                throw new Error('Ошибка сетевого соединения');
            }
            return response.json();
        })
        .then(data => {
            queriesTable.innerHTML = '';

            if (data.length === 0) {
                queriesTable.innerHTML = `
                    <tr>
                        <td colspan="5" class="text-center">
                            <div class="empty-state p-4 text-center">
                                <div class="empty-state-icon mb-3">
                                    <i class="fas fa-search fa-3x text-muted"></i>
                                </div>
                                <h3 class="empty-state-title">Нет истории запросов</h3>
                                <p class="empty-state-description">Здесь будет отображаться история ваших запросов</p>
                            </div>
                        </td>
                    </tr>
                `;
                return;
            }

            data.forEach(query => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${formatDate(query.created_at)}</td>
                    <td>${query.vin || '-'}</td>
                    <td>${query.marka || '-'}</td>
                    <td>${query.tip || 'Стандартный'}</td>
                    <td>${query.cost} ₽</td>
                `;
                queriesTable.appendChild(row);
            });
        })
        .catch(error => {
            console.error('Error loading queries:', error);
            queriesTable.innerHTML = '<tr><td colspan="5" class="text-center text-danger">Ошибка при загрузке истории запросов</td></tr>';
        });
}

function formatDate(dateString) {
    if (!dateString) return '-';

    const date = new Date(dateString);
    return new Intl.DateTimeFormat('ru-RU', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
    }).format(date);
}