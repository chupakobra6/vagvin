function updateProgress(elementId, duration = 10000) {
    const progressBar = document.getElementById(elementId + '_progress');
    const progressText = document.getElementById(elementId + '_progress_text');
    const progressContainer = document.getElementById(elementId + '_progress_container');
    
    progressContainer.style.display = 'block';
    
    let startTime = Date.now();
    let interval = setInterval(function() {
        let elapsedTime = Date.now() - startTime;
        let progress = Math.min(Math.floor((elapsedTime / duration) * 100), 99);
        
        progressBar.value = progress;
        progressText.textContent = progress + '%';
        
        if (progress >= 99) {
            clearInterval(interval);
        }
    }, 200);
    
    return function stopProgress(success = true) {
        clearInterval(interval);
        progressBar.value = 100;
        progressText.textContent = '100%';
        
        setTimeout(() => {
            progressContainer.style.display = 'none';
        }, 500);
    };
}

function displayResult(elementId, data) {
    const resultElement = document.getElementById(elementId + '_result');
    resultElement.style.display = 'block';
    
    console.log(`${elementId} API Response:`, data);
    
    let html = '';
    
    if (data.error) {
        html = `<p class="error-message"><i class="fas fa-exclamation-triangle me-2"></i>${data.error}</p>`;
    } else if (data.success === false) {
        html = `<p class="warning-message"><i class="fas fa-exclamation-circle me-2"></i>${data.message}</p>`;
    } else if (data.success === true) {
        html = `<p class="success-message"><i class="fas fa-check-circle me-2"></i>${data.message || 'Данные найдены!'}</p>`;
        
        const resultTable = document.createElement('table');
        resultTable.className = 'result-table';
        
        if (elementId === 'autoteka' && data.data) {
            for (const [key, value] of Object.entries(data.data)) {
                addTableRow(resultTable, formatFieldName(key), formatValue(value));
            }
        } else if (elementId === 'carfax' && data.vehicle_info) {
            addTableRow(resultTable, 'Автомобиль', data.vehicle_info);
            addTableRow(resultTable, 'Записи в базе CARFAX', data.carfax || 0);
            addTableRow(resultTable, 'Записи в базе Autocheck', data.autocheck || 0);
        } else if (elementId === 'vinhistory' && data.vehicle) {
            addTableRow(resultTable, 'Автомобиль', data.vehicle);
            addTableRow(resultTable, 'Количество фотографий', data.images_count || 0);
        } else if (elementId === 'auction' && data.auction_count) {
            addTableRow(resultTable, 'Количество записей аукционов', data.auction_count);
        } else {
            for (const [key, value] of Object.entries(data)) {
                if (key === 'success' || key === 'message' || key === 'error') {
                    continue;
                }
                
                if (typeof value === 'object' && value !== null) {
                    if (Array.isArray(value)) {
                        addTableRow(resultTable, formatFieldName(key), formatArrayValue(value));
                    } else {
                        const headingRow = document.createElement('tr');
                        const headingCell = document.createElement('td');
                        headingCell.colSpan = 2;
                        headingCell.className = 'result-section-heading';
                        headingCell.textContent = formatFieldName(key);
                        headingRow.appendChild(headingCell);
                        resultTable.appendChild(headingRow);
                        
                        processDataObject(resultTable, value);
                    }
                } else {
                    addTableRow(resultTable, formatFieldName(key), formatValue(value));
                }
            }
        }
        
        if (resultTable.rows.length > 0) {
            html += resultTable.outerHTML;
        }
    } else {
        html = '<div class="result-container">';
        
        html += '<p class="info-message"><i class="fas fa-info-circle me-2"></i>Получены данные:</p>';
        
        const resultTable = document.createElement('table');
        resultTable.className = 'result-table';
        
        processDataObject(resultTable, data);
        
        if (resultTable.rows.length > 0) {
            html += resultTable.outerHTML;
        } else {
            html += '<p>Нет данных для отображения</p>';
        }
        
        html += '</div>';
    }
    
    resultElement.innerHTML = html;
}

function processDataObject(table, dataObj, prefix = '') {
    if (!dataObj || typeof dataObj !== 'object') return;
    
    for (const [key, value] of Object.entries(dataObj)) {
        if (typeof value === 'object' && value !== null && !Array.isArray(value)) {
            const headingRow = document.createElement('tr');
            const headingCell = document.createElement('td');
            headingCell.colSpan = 2;
            headingCell.className = 'result-section-heading';
            headingCell.textContent = formatFieldName(key);
            headingRow.appendChild(headingCell);
            table.appendChild(headingRow);
            
            processDataObject(table, value, prefix + key + '.');
        } else {
            const fieldName = prefix ? prefix + key : key;
            addTableRow(table, formatFieldName(fieldName), formatValue(value));
        }
    }
}

function addTableRow(table, label, value) {
    const row = document.createElement('tr');
    
    const labelCell = document.createElement('td');
    labelCell.className = 'result-label';
    labelCell.textContent = label + ':';
    
    const valueCell = document.createElement('td');
    valueCell.className = 'result-value';
    
    if (typeof value === 'string' && value.startsWith('<span')) {
        valueCell.innerHTML = value;
    } else {
        valueCell.textContent = value;
    }
    
    row.appendChild(labelCell);
    row.appendChild(valueCell);
    table.appendChild(row);
}

function formatFieldName(fieldName) {
    return fieldName
        .replace(/([A-Z])/g, ' $1')
        .replace(/^./, str => str.toUpperCase())
        .replace(/\bvin\b/i, 'VIN')
        .replace(/\bгн\b/i, 'ГН')
        .replace(/\bid\b/i, 'ID')
        .replace(/V I N/i, 'VIN')
        .replace(/Г Н/i, 'ГН')
        .replace(/I D/i, 'ID')
        .replace(/VIN\/ГН\/ID/i, 'VIN / ГН / ID')
        .replace(/VIN\/ГН\/ ID/i, 'VIN / ГН / ID')
        .trim();
}

function formatValue(value) {
    if (Array.isArray(value)) {
        return formatArrayValue(value);
    } else if (typeof value === 'boolean') {
        return value ? 
            '<span class="badge bg-success">Да</span>' : 
            '<span class="badge bg-danger">Нет</span>';
    } else if (value === null || value === undefined) {
        return '—';
    } else if (typeof value === 'number') {
        return value.toString();
    } else {
        return value.toString();
    }
}

function formatArrayValue(array) {
    if (array.length === 0) return '—';
    
    if (array.length < 5) {
        return array.join(', ');
    }
    
    return array.join(', ');
}

function checkAutoteka() {
    const input = document.getElementById('autoteka_input').value.trim();
    if (!input) {
        alert('Пожалуйста, введите VIN, Госномер или ссылку на объявление Avito');
        return;
    }
    
    document.getElementById('autoteka_input').disabled = true;
    document.getElementById('autoteka_button').disabled = true;
    document.getElementById('autoteka_loader').style.display = 'block';
    document.getElementById('autoteka_result').style.display = 'none';
    
    const stopProgress = updateProgress('autoteka', 20000);
    
    let params = {};
    let searchType = '';
    
    if (input.includes('avito.ru')) {
        params = { avitoUrl: input };
        searchType = 'Avito URL';
    } else if (/^[A-HJ-NPR-Z0-9]{17}$/i.test(input)) {
        params = { vin: input.toUpperCase() };
        searchType = 'VIN';
    } else {
        params = { regNumber: input };
        searchType = 'Госномер';
    }
    
    console.log(`Checking Autoteka with ${searchType}: ${Object.values(params)[0]}`);
    
    fetch(`/reports/api/check/autoteka/?${new URLSearchParams(params)}`)
        .then(response => response.json())
        .then(data => {
            stopProgress();
            displayResult('autoteka', data);
            
            fetchRecentQueries();
        })
        .catch(error => {
            stopProgress(false);
            document.getElementById('autoteka_result').innerHTML = `<p class="error-message"><i class="fas fa-exclamation-triangle me-2"></i>Ошибка при запросе: ${error.message}</p>`;
            document.getElementById('autoteka_result').style.display = 'block';
            console.error('Autoteka API error:', error);
        })
        .finally(() => {
            document.getElementById('autoteka_loader').style.display = 'none';
            document.getElementById('autoteka_input').disabled = false;
            document.getElementById('autoteka_button').disabled = false;
        });
}

function checkCarfax() {
    const input = document.getElementById('carfax_input').value.trim();
    if (!input) {
        alert('Пожалуйста, введите VIN');
        return;
    }
    
    if (!/^[A-HJ-NPR-Z0-9]{17}$/i.test(input)) {
        alert('Пожалуйста, введите корректный VIN (17 символов)');
        return;
    }
    
    const vin = input.toUpperCase();
    console.log(`Checking Carfax with VIN: ${vin}`);
    
    document.getElementById('carfax_input').disabled = true;
    document.getElementById('carfax_button').disabled = true;
    document.getElementById('carfax_loader').style.display = 'block';
    document.getElementById('carfax_result').style.display = 'none';
    
    const stopProgress = updateProgress('carfax', 15000);
    
    fetch(`/reports/api/check/carfax-autocheck/?vin=${vin}`)
        .then(response => response.json())
        .then(data => {
            stopProgress();
            displayResult('carfax', data);
            
            fetchRecentQueries();
        })
        .catch(error => {
            stopProgress(false);
            document.getElementById('carfax_result').innerHTML = `<p class="error-message"><i class="fas fa-exclamation-triangle me-2"></i>Ошибка при запросе: ${error.message}</p>`;
            document.getElementById('carfax_result').style.display = 'block';
            console.error('Carfax API error:', error);
        })
        .finally(() => {
            document.getElementById('carfax_loader').style.display = 'none';
            document.getElementById('carfax_input').disabled = false;
            document.getElementById('carfax_button').disabled = false;
        });
}

function checkVinhistory() {
    const input = document.getElementById('vinhistory_input').value.trim();
    if (!input) {
        alert('Пожалуйста, введите VIN');
        return;
    }
    
    if (!/^[A-HJ-NPR-Z0-9]{17}$/i.test(input)) {
        alert('Пожалуйста, введите корректный VIN (17 символов)');
        return;
    }
    
    const vin = input.toUpperCase();
    console.log(`Checking Vinhistory with VIN: ${vin}`);
    
    document.getElementById('vinhistory_input').disabled = true;
    document.getElementById('vinhistory_button').disabled = true;
    document.getElementById('vinhistory_loader').style.display = 'block';
    document.getElementById('vinhistory_result').style.display = 'none';
    
    const stopProgress = updateProgress('vinhistory', 15000);
    
    fetch(`/reports/api/check/vinhistory/?vin=${vin}`)
        .then(response => response.json())
        .then(data => {
            stopProgress();
            displayResult('vinhistory', data);
            
            fetchRecentQueries();
        })
        .catch(error => {
            stopProgress(false);
            document.getElementById('vinhistory_result').innerHTML = `<p class="error-message"><i class="fas fa-exclamation-triangle me-2"></i>Ошибка при запросе: ${error.message}</p>`;
            document.getElementById('vinhistory_result').style.display = 'block';
            console.error('Vinhistory API error:', error);
        })
        .finally(() => {
            document.getElementById('vinhistory_loader').style.display = 'none';
            document.getElementById('vinhistory_input').disabled = false;
            document.getElementById('vinhistory_button').disabled = false;
        });
}

function checkAuction() {
    const input = document.getElementById('auction_input').value.trim();
    if (!input) {
        alert('Пожалуйста, введите VIN');
        return;
    }
    
    if (!/^[A-HJ-NPR-Z0-9]{17}$/i.test(input)) {
        alert('Пожалуйста, введите корректный VIN (17 символов)');
        return;
    }
    
    const vin = input.toUpperCase();
    console.log(`Checking Auction with VIN: ${vin}`);
    
    document.getElementById('auction_input').disabled = true;
    document.getElementById('auction_button').disabled = true;
    document.getElementById('auction_loader').style.display = 'block';
    document.getElementById('auction_result').style.display = 'none';
    
    const stopProgress = updateProgress('auction', 15000);
    
    fetch(`/reports/api/check/auction/?vin=${vin}`)
        .then(response => response.json())
        .then(data => {
            stopProgress();
            displayResult('auction', data);
            
            fetchRecentQueries();
        })
        .catch(error => {
            stopProgress(false);
            document.getElementById('auction_result').innerHTML = `<p class="error-message"><i class="fas fa-exclamation-triangle me-2"></i>Ошибка при запросе: ${error.message}</p>`;
            document.getElementById('auction_result').style.display = 'block';
            console.error('Auction API error:', error);
        })
        .finally(() => {
            document.getElementById('auction_loader').style.display = 'none';
            document.getElementById('auction_input').disabled = false;
            document.getElementById('auction_button').disabled = false;
        });
}

function fetchRecentQueries() {
    const container = document.getElementById('queries-container');
    if (!container) {
        console.error('Element with ID "queries-container" not found.');
        return;
    }
    
    container.innerHTML = '<div class="text-center p-3"><div class="spinner-border spinner-border-sm text-primary" role="status"><span class="visually-hidden">Загрузка...</span></div> <span class="ms-2 text-muted">Загрузка истории запросов...</span></div>';
    
    fetch('/reports/api/recent-queries/')
        .then(response => {
            if (!response.ok) {
                throw new Error(`Ошибка сети: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            container.innerHTML = '';
            
            if (!Array.isArray(data)) {
                console.error('Recent queries API did not return an array:', data);
                container.innerHTML = '<div class="alert alert-warning">Не удалось загрузить историю запросов: неверный формат данных.</div>';
                return;
            }

            if (data.length === 0) {
                container.innerHTML = '<div class="text-center p-3 text-muted">История запросов пуста.</div>';
                return;
            }
            
            const table = document.createElement('table');
            table.className = 'table table-hover table-striped';
            const thead = document.createElement('thead');
            thead.innerHTML = `
                <tr>
                    <th>Дата и время</th>
                    <th>Сервис</th>
                    <th>Идентификатор</th>
                </tr>
            `;
            const tbody = document.createElement('tbody');
            
            data.forEach(queryStr => {
                const match = queryStr.match(/^(\d{2}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2}).*проверку\s(\S+)\s.*(?:VIN|ГН|ID|Avito ID)\s+(\S+.*)$/i) || 
                              queryStr.match(/^(\d{2}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2})\s+(\S+)\s+(\S+.*)$/i);
                
                let timestamp = 'N/A';
                let serviceType = 'N/A';
                let identifier = 'N/A';

                if (match) {
                    timestamp = match[1];
                    serviceType = formatServiceType(match[2]);
                    identifier = match[3];
                } else {
                    console.warn('Could not parse query string:', queryStr);
                    identifier = queryStr;
                }
                
                const row = tbody.insertRow();
                row.innerHTML = `
                    <td>${timestamp}</td>
                    <td>${serviceType}</td>
                    <td>${identifier}</td>
                `;
            });
            
            table.appendChild(thead);
            table.appendChild(tbody);
            container.appendChild(table);
        })
        .catch(error => {
            console.error('Error fetching recent queries:', error);
            container.innerHTML = `<div class="alert alert-danger">Ошибка при загрузке истории запросов: ${error.message}</div>`;
        });
}

function formatServiceType(typeKey) {
    const serviceTypes = {
        'autoteka': 'Автотека (VIN)',
        'autoteka_reg': 'Автотека (Госномер)',
        'autoteka_avito': 'Автотека (Avito)',
        'carfax': 'Carfax / Autocheck',
        'vinhistory': 'Vinhistory',
        'auction': 'Аукционы',
        'basic': 'Базовый отчет',
        'full': 'Полный отчет',
        'unified': 'Комплексная проверка'
    };
    return serviceTypes[typeKey.toLowerCase()] || typeKey;
}

document.addEventListener('DOMContentLoaded', function() {
    fetchRecentQueries();
    
    setInterval(fetchRecentQueries, 15000);
});
