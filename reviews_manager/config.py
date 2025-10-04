"""
Конфигурационный файл для системы управления отзывами
"""


DB_CONFIG = {
    'host': 'mpsp.online',  # Хост MySQL сервера
    'user': 'u3054108_Mukam1',  # Имя пользователя
    'password': 'vYL-f2w-cNk-fuJ',  # Пароль
    'database': 'u3054108_reviews_db',  # Имя базы данных
    'charset': 'utf8mb4',  # Кодировка
    'collation': 'utf8mb4_unicode_ci'  # Явно указываем поддерживаемое сопоставление для MySQL 5.7
}

# URL и пути сайта
SITE_CONFIG = {
    'base_url': 'https://mpsp.online',  # Базовый URL сайта
    'api_path': '/api/reviews.php',  # Путь к API для работы с отзывами
    'reviews_page': '/submit-review.html'  # Страница для отправки отзывов
}

# Структура таблиц базы данных
DB_TABLES = {
    'reviews': {
        'name': 'reviews',  # Название таблицы отзывов
        'fields': {
            'id': 'INT AUTO_INCREMENT PRIMARY KEY',
            'order_id': 'VARCHAR(100)',
            'token': 'VARCHAR(100)',
            'name': 'VARCHAR(100)',
            'service': 'VARCHAR(100)',
            'rating': 'INT',
            'text': 'TEXT',
            'date': 'DATETIME DEFAULT CURRENT_TIMESTAMP',
            'status': 'VARCHAR(20) DEFAULT "pending"',
            'response': 'TEXT',
            'likes': 'INT DEFAULT 0',
            'dislikes': 'INT DEFAULT 0'
        }
    },
    'contacts': {
        'name': 'contacts',  # Название таблицы контактов
        'fields': {
            'id': 'INT AUTO_INCREMENT PRIMARY KEY',
            'name': 'VARCHAR(100)',
            'email': 'VARCHAR(100)',
            'phone': 'VARCHAR(50)',
            'message': 'TEXT',
            'date': 'DATETIME DEFAULT CURRENT_TIMESTAMP',
            'status': 'VARCHAR(20) DEFAULT "new"'
        }
    }
}

# Настройки API
API_CONFIG = {
    'allowed_methods': ['GET', 'POST'],
    'allowed_actions': ['get_reviews', 'add_review', 'update_reaction',
                        'approve_review', 'reject_review', 'add_response'],
    'success_codes': [200],
    'timeout': 10  # Таймаут для API запросов в секундах
}

# Настройки приложения
APP_CONFIG = {
    'name': 'MPSP Reviews Manager',
    'version': '1.0.0',
    'log_file': 'reviews_manager.log',
    'log_level': 'INFO',
    'default_page_size': 10,
    'available_statuses': [
        {'value': 'pending', 'label': 'Ожидает модерации'},
        {'value': 'approved', 'label': 'Одобрено'},
        {'value': 'rejected', 'label': 'Отклонено'}
    ],
    'available_ratings': [5, 4, 3, 2, 1]
}

# SQL запросы для создания таблиц (если нужно создавать таблицы программно)
CREATE_TABLES_SQL = [
    """
    CREATE TABLE IF NOT EXISTS reviews (
        id INT AUTO_INCREMENT PRIMARY KEY,
        order_id VARCHAR(100),
        token VARCHAR(100),
        name VARCHAR(100),
        service VARCHAR(100),
        rating INT,
        text TEXT,
        date DATETIME DEFAULT CURRENT_TIMESTAMP,
        status VARCHAR(20) DEFAULT 'pending',
        response TEXT,
        likes INT DEFAULT 0,
        dislikes INT DEFAULT 0
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS contacts (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(100),
        email VARCHAR(100),
        phone VARCHAR(50),
        message TEXT,
        date DATETIME DEFAULT CURRENT_TIMESTAMP,
        status VARCHAR(20) DEFAULT 'new'
    );
    """
]
# Учетные данные для авторизации в админ-панели
ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = 'mpsp2023admin'

# Настройки приложения
APP_NAME = 'MPSP Reviews Manager'
APP_VERSION = '1.0.0'
LOG_FILE = 'mpsp_reviews.log'

# Настройки интерфейса
DEFAULT_WINDOW_WIDTH = 1000
DEFAULT_WINDOW_HEIGHT = 600