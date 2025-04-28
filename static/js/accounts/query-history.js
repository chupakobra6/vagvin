document.addEventListener('DOMContentLoaded', function() {
    loadUserQueries();
});

/**
 * Load user queries history
 */
function loadUserQueries() {
    const queriesTable = document.getElementById('queries-table');
    if (!queriesTable) return;
    
    fetch(queriesTable.dataset.url)
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            queriesTable.innerHTML = '';
            
            if (data.length === 0) {
                queriesTable.innerHTML = '<tr><td colspan="5" class="text-center">У вас пока нет запросов</td></tr>';
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

/**
 * Format date string to local format
 */
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