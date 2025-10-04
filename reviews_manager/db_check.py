# Файл reviews_manager/db_check.py

import mysql.connector
import socket


def check_db_connection():
    """
    Проверяет возможность подключения к базе данных

    Returns:
        bool: True, если соединение возможно, False в противном случае
    """
    try:
        # Проверяем доступность хоста (быстрая проверка)
        host = 'mpsp.online'
        port = 3306  # Стандартный порт MySQL

        print(f"Проверка доступности хоста {host}:{port}...")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)  # Таймаут 2 секунды
        result = sock.connect_ex((host, port))
        sock.close()

        if result != 0:
            print(f"Не удалось подключиться к хосту {host}:{port}")
            return False

        # Если хост доступен, пробуем подключиться к БД
        from reviews_manager.config import DB_CONFIG
        try:
            from reviews_manager.config import DB_CONFIG
            db_config = DB_CONFIG.copy()
        except ImportError:
            db_config = {
                'host': 'mpsp.online',
                'user': 'u3054108_Mukam1',
                'password': 'vYL-f2w-cNk-fuJ',
                'database': 'u3054108_reviews_db',
                'charset': 'utf8mb4',
                'collation': 'utf8mb4_unicode_ci'
            }
        db_config['host'] = host
        db_config['connect_timeout'] = 5  # Таймаут 5 секунд

        # Добавляем параметры для решения проблемы с сопоставлением
        if 'collation' not in db_config:
            db_config['collation'] = 'utf8mb4_unicode_ci'  # Поддерживаемое в MySQL 5.7

        print(f"Попытка подключения к БД: {db_config}")
        connection = mysql.connector.connect(**db_config)
        connection.close()

        print("Подключение к БД успешно установлено")
        return True

    except Exception as e:
        print(f"Ошибка при проверке соединения с БД: {e}")
        import traceback
        traceback.print_exc()

        # Если ошибка связана с сопоставлением, попробуем ещё раз с другим сопоставлением
        if "Unknown collation" in str(e):
            try:
                print("Пробуем подключиться с другим сопоставлением...")
                from reviews_manager.config import DB_CONFIG
                try:
                    from reviews_manager.config import DB_CONFIG
                    db_config = DB_CONFIG.copy()
                except ImportError:
                    db_config = {
                        'host': 'mpsp.online',
                        'user': 'u3054108_Mukam1',
                        'password': 'vYL-f2w-cNk-fuJ',
                        'database': 'u3054108_reviews_db',
                        'charset': 'utf8mb4',
                        'collation': 'utf8mb4_unicode_ci'
                    }
                db_config['host'] = host
                db_config['connect_timeout'] = 5
                db_config['charset'] = 'utf8'  # Используем простой utf8 вместо utf8mb4
                if 'collation' in db_config:
                    del db_config['collation']  # Удаляем параметр collation

                print(f"Новая попытка подключения: {db_config}")
                connection = mysql.connector.connect(**db_config)
                connection.close()
                print("Подключение успешно со вторым набором параметров")
                return True
            except Exception as e2:
                print(f"Вторая попытка также не удалась: {e2}")
                return False

        return False