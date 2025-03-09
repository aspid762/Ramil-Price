// Функция для инициализации всплывающих подсказок Bootstrap
function initTooltips() {
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// Функция для подтверждения удаления
function confirmDelete(event, message) {
    if (!confirm(message || 'Вы уверены, что хотите удалить этот элемент?')) {
        event.preventDefault();
        return false;
    }
    return true;
}

// Функция для переключения бокового меню на мобильных устройствах
function toggleSidebar() {
    document.body.classList.toggle('sidebar-expanded');
}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    // Инициализация всплывающих подсказок
    initTooltips();
    
    // Добавление обработчиков для кнопок удаления
    document.querySelectorAll('.btn-delete').forEach(function(button) {
        button.addEventListener('click', function(event) {
            return confirmDelete(event, this.getAttribute('data-confirm-message'));
        });
    });
    
    // Обработчик для переключения бокового меню
    var sidebarToggle = document.getElementById('sidebarToggle');
    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', toggleSidebar);
    }
    
    // Инициализация выпадающих меню в боковой панели
    var dropdowns = document.querySelectorAll('.sidebar .dropdown-toggle');
    dropdowns.forEach(function(dropdown) {
        dropdown.addEventListener('click', function(e) {
            if (window.innerWidth < 768 && !document.body.classList.contains('sidebar-expanded')) {
                e.preventDefault();
                e.stopPropagation();
                toggleSidebar();
            }
        });
    });
    
    // Инициализация графиков на главной странице
    initDashboardCharts();
});

// Функция для инициализации графиков на главной странице
function initDashboardCharts() {
    // График продаж
    var salesChartEl = document.getElementById('salesChart');
    if (salesChartEl) {
        var salesChart = new Chart(salesChartEl, {
            type: 'line',
            data: {
                labels: ['Янв', 'Фев', 'Мар', 'Апр', 'Май', 'Июн', 'Июл', 'Авг', 'Сен', 'Окт', 'Ноя', 'Дек'],
                datasets: [{
                    label: 'Продажи',
                    data: [12, 19, 3, 5, 2, 3, 20, 33, 23, 12, 33, 55],
                    borderColor: '#3498db',
                    backgroundColor: 'rgba(52, 152, 219, 0.1)',
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    }
    
    // График популярных товаров
    var productsChartEl = document.getElementById('productsChart');
    if (productsChartEl) {
        var productsChart = new Chart(productsChartEl, {
            type: 'bar',
            data: {
                labels: ['Проф. труба', 'Уголок', 'Труба круг.', 'Профнастил', 'Арматура'],
                datasets: [{
                    label: 'Продажи',
                    data: [42, 29, 33, 15, 22],
                    backgroundColor: [
                        'rgba(52, 152, 219, 0.7)',
                        'rgba(46, 204, 113, 0.7)',
                        'rgba(155, 89, 182, 0.7)',
                        'rgba(241, 196, 15, 0.7)',
                        'rgba(231, 76, 60, 0.7)'
                    ],
                    borderColor: [
                        'rgba(52, 152, 219, 1)',
                        'rgba(46, 204, 113, 1)',
                        'rgba(155, 89, 182, 1)',
                        'rgba(241, 196, 15, 1)',
                        'rgba(231, 76, 60, 1)'
                    ],
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    }
} 