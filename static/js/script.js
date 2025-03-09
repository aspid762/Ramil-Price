// Функция для инициализации всплывающих подсказок
function initTooltips() {
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// Функция для инициализации всплывающих окон
function initPopovers() {
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
}

// Функция для подтверждения удаления
function confirmDelete(event) {
    var button = event.submitter;
    var message = button.getAttribute('data-confirm-message') || 'Вы уверены, что хотите удалить этот элемент?';
    
    if (!confirm(message)) {
        event.preventDefault();
        return false;
    }
    
    return true;
}

// Функция для форматирования чисел
function formatNumber(number, decimals = 2) {
    return number.toLocaleString('ru-RU', {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals
    });
}

// Функция для форматирования даты
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('ru-RU');
}

// Функция для автоматического расчета цены за метр
function calculatePricePerMeter() {
    const pricePerTonInput = document.getElementById('price_per_ton');
    const weightPerMeterInput = document.getElementById('weight_per_meter');
    const pricePerMeterDisplay = document.getElementById('price_per_meter_display');
    
    if (pricePerTonInput && weightPerMeterInput && pricePerMeterDisplay) {
        const calculateAndDisplay = function() {
            const pricePerTon = parseFloat(pricePerTonInput.value) || 0;
            const weightPerMeter = parseFloat(weightPerMeterInput.value) || 0;
            
            // Расчет цены за метр: (цена за тонну * вес метра в кг) / 1000
            const pricePerMeter = (pricePerTon * weightPerMeter) / 1000;
            
            // Отображение с форматированием
            pricePerMeterDisplay.textContent = formatNumber(pricePerMeter);
        };
        
        // Вычисляем при загрузке страницы
        calculateAndDisplay();
        
        // Добавляем обработчики событий для пересчета при изменении значений
        pricePerTonInput.addEventListener('input', calculateAndDisplay);
        weightPerMeterInput.addEventListener('input', calculateAndDisplay);
    }
}

// Функция для фильтрации таблиц
function initTableFilter() {
    const filterInput = document.getElementById('table-filter');
    const table = document.getElementById('filterable-table');
    
    if (filterInput && table) {
        filterInput.addEventListener('keyup', function() {
            const filterValue = this.value.toLowerCase();
            const rows = table.querySelectorAll('tbody tr');
            
            rows.forEach(function(row) {
                const text = row.textContent.toLowerCase();
                if (text.indexOf(filterValue) > -1) {
                    row.style.display = '';
                } else {
                    row.style.display = 'none';
                }
            });
        });
    }
}

// Функция для динамического добавления полей в форму
function initDynamicForm() {
    const addButton = document.getElementById('add-field-button');
    const fieldsContainer = document.getElementById('dynamic-fields-container');
    const template = document.getElementById('field-template');
    
    if (addButton && fieldsContainer && template) {
        let fieldCounter = 0;
        
        addButton.addEventListener('click', function() {
            fieldCounter++;
            
            // Клонируем шаблон
            const newField = template.content.cloneNode(true);
            
            // Обновляем ID и атрибуты
            const inputs = newField.querySelectorAll('input, select, textarea');
            inputs.forEach(function(input) {
                const name = input.getAttribute('name');
                if (name) {
                    input.setAttribute('name', name + '_' + fieldCounter);
                    input.setAttribute('id', name + '_' + fieldCounter);
                }
            });
            
            // Добавляем кнопку удаления
            const removeButton = document.createElement('button');
            removeButton.type = 'button';
            removeButton.className = 'btn btn-sm btn-danger mt-2';
            removeButton.innerHTML = '<i class="fas fa-trash"></i> Удалить';
            removeButton.addEventListener('click', function() {
                this.closest('.dynamic-field').remove();
            });
            
            newField.querySelector('.dynamic-field').appendChild(removeButton);
            
            // Добавляем новое поле в контейнер
            fieldsContainer.appendChild(newField);
        });
    }
}

// Функция для предварительного просмотра изображений
function initImagePreview() {
    const imageInputs = document.querySelectorAll('.image-input');
    
    imageInputs.forEach(function(input) {
        const previewContainer = document.getElementById(input.getAttribute('data-preview'));
        
        if (previewContainer) {
            input.addEventListener('change', function() {
                previewContainer.innerHTML = '';
                
                if (this.files && this.files[0]) {
                    const reader = new FileReader();
                    
                    reader.onload = function(e) {
                        const img = document.createElement('img');
                        img.src = e.target.result;
                        img.className = 'img-thumbnail mt-2';
                        img.style.maxHeight = '200px';
                        previewContainer.appendChild(img);
                    }
                    
                    reader.readAsDataURL(this.files[0]);
                }
            });
        }
    });
}

/**
 * Копирует текст в буфер обмена
 * @param {string} text - Текст для копирования
 * @param {HTMLElement} button - Кнопка, которая была нажата
 */
function copyToClipboard(text, button) {
    // Создаем временный элемент для копирования
    const textarea = document.createElement('textarea');
    textarea.value = text;
    document.body.appendChild(textarea);
    textarea.select();
    
    try {
        // Копируем текст в буфер обмена
        document.execCommand('copy');
        
        // Меняем иконку на галочку на короткое время
        const originalHTML = button.innerHTML;
        button.innerHTML = '<i class="fas fa-check"></i>';
        button.classList.add('btn-success');
        button.classList.remove('btn-outline-secondary');
        
        // Возвращаем оригинальную иконку через 1.5 секунды
        setTimeout(() => {
            button.innerHTML = originalHTML;
            button.classList.remove('btn-success');
            button.classList.add('btn-outline-secondary');
        }, 1500);
    } catch (err) {
        console.error('Не удалось скопировать текст: ', err);
    }
    
    // Удаляем временный элемент
    document.body.removeChild(textarea);
}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    initTooltips();
    initPopovers();
    calculatePricePerMeter();
    initTableFilter();
    initDynamicForm();
    initImagePreview();
    
    // Инициализация подтверждения удаления для всех форм с классом 'delete-form'
    document.querySelectorAll('.delete-form').forEach(function(form) {
        form.addEventListener('submit', confirmDelete);
    });
}); 