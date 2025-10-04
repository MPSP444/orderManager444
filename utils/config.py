import os
from pathlib import Path

# Базовая директория проекта
BASE_DIR = Path(__file__).resolve().parent.parent

# Путь к файлу базы данных
DATABASE_PATH = os.path.join(BASE_DIR, 'users.db')

# Путь к файлу с последним пользователем
LAST_USER_FILE = os.path.join(BASE_DIR, 'last_user.txt')

# Настройки администратора по умолчанию
DEFAULT_ADMIN = {
    'full_name': 'Administrator',
    'password': 'admin123',  # В реальном приложении нужно использовать безопасный пароль
}