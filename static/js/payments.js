document.addEventListener('DOMContentLoaded', function() {
    const amountButtons = document.querySelectorAll('.payment-amount-btn');
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
                parentForm.querySelectorAll('.payment-amount-btn').forEach(btn => {
                    btn.classList.remove('active', 'btn-primary');
                    btn.classList.add('btn-outline-primary');
                });
                this.classList.remove('btn-outline-primary');
                this.classList.add('btn-primary', 'active');
            }
        });
    });

    const copyButtons = document.querySelectorAll('.copy-btn');
    copyButtons.forEach(function(btn) {
        btn.addEventListener('click', function(event) {
            event.preventDefault();
            const targetId = btn.getAttribute('data-copy-target');
            const text = document.getElementById(targetId).textContent;
            
            const textarea = document.createElement('textarea');
            textarea.value = text;
            textarea.style.position = 'absolute';
            textarea.style.left = '-9999px';
            document.body.appendChild(textarea);
            textarea.select();
            document.execCommand('copy');
            document.body.removeChild(textarea);
            
            const icon = btn.querySelector('i');
            const originalClass = icon.className;
            icon.className = 'fas fa-check text-success';
            setTimeout(() => {
                icon.className = originalClass;
            }, 2000);
        });
    });
}); 