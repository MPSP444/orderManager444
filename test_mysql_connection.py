"""
Скрипт для подключения к базе данных отзывов и отображения всех записей
"""

import mysql.connector
import sys
from tabulate import tabulate  # Для красивого форматирования таблиц

# Импорт конфигурации из config.py
try:
    from reviews_manager.config import DB_CONFIG, DB_TABLES
    print(f"Конфигурация успешно импортирована")

    # Корректируем хост для использования домена сайта
    DB_CONFIG['host'] = 'mpsp.online'
    print(f"Используем хост: {DB_CONFIG['host']}")

except ImportError as e:
    print(f"Ошибка импорта конфигурации: {e}")
    sys.exit(1)

def fetch_and_display_data():
    """Подключение к БД и отображение всех таблиц и их данных"""

    print(f"Подключаемся к MySQL на {DB_CONFIG['host']}...")

    try:
        # Устанавливаем соединение
        connection = mysql.connector.connect(
            host=DB_CONFIG['host'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            database=DB_CONFIG['database'],
            charset=DB_CONFIG['charset']
        )

        if connection.is_connected():
            db_info = connection.get_server_info()
            print(f"Подключено к MySQL Server версии: {db_info}")

            cursor = connection.cursor(dictionary=True)

            # Получаем список всех таблиц
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()

            table_key = f"Tables_in_{DB_CONFIG['database']}"
            print(f"\nТаблицы в базе данных {DB_CONFIG['database']}:")
            for i, table_data in enumerate(tables, 1):
                table_name = table_data[table_key]
                print(f"{i}. {table_name}")

            # Для каждой таблицы выводим структуру и данные
            for table_data in tables:
                table_name = table_data[table_key]
                print(f"\n{'=' * 80}")
                print(f"Таблица: {table_name}")
                print(f"{'=' * 80}")

                # Получаем структуру таблицы
                cursor.execute(f"DESCRIBE {table_name}")
                structure = cursor.fetchall()

                print("\nСтруктура таблицы:")
                headers = structure[0].keys()
                rows = [list(row.values()) for row in structure]
                print(tabulate(rows, headers=headers, tablefmt="grid"))

                # Получаем количество записей
                cursor.execute(f"SELECT COUNT(*) as count FROM {table_name}")
                count = cursor.fetchone()['count']
                print(f"\nКоличество записей: {count}")

                if count > 0:
                    # Получаем данные (с ограничением)
                    max_rows = 20  # Максимальное количество строк для отображения
                    cursor.execute(f"SELECT * FROM {table_name} LIMIT {max_rows}")
                    data = cursor.fetchall()

                    if data:
                        print(f"\nДанные из таблицы (первые {min(max_rows, count)} записей):")
                        headers = data[0].keys()
                        rows = [list(row.values()) for row in data]

                        # Ограничиваем длину текстовых полей для удобства отображения
                        max_length = 50
                        trimmed_rows = []
                        for row in rows:
                            trimmed_row = []
                            for value in row:
                                if isinstance(value, str) and len(value) > max_length:
                                    trimmed_row.append(value[:max_length] + "...")
                                else:
                                    trimmed_row.append(value)
                            trimmed_rows.append(trimmed_row)

                        print(tabulate(trimmed_rows, headers=headers, tablefmt="grid"))

                        if count > max_rows:
                            print(f"\nПоказаны только первые {max_rows} из {count} записей.")

            # Дополнительная статистика для таблицы отзывов
            reviews_table = DB_TABLES['reviews']['name']
            if reviews_table in [table_data[table_key] for table_data in tables]:
                print(f"\n{'=' * 80}")
                print(f"Статистика по отзывам")
                print(f"{'=' * 80}")

                # Статистика по рейтингам
                cursor.execute(f"""
                    SELECT rating, COUNT(*) as count 
                    FROM {reviews_table} 
                    GROUP BY rating 
                    ORDER BY rating DESC
                """)
                ratings = cursor.fetchall()

                if ratings:
                    print("\nРаспределение рейтингов:")
                    headers = ['Рейтинг', 'Количество']
                    rows = [[r['rating'], r['count']] for r in ratings]
                    print(tabulate(rows, headers=headers, tablefmt="grid"))

                # Статистика по статусам
                cursor.execute(f"""
                    SELECT status, COUNT(*) as count 
                    FROM {reviews_table} 
                    GROUP BY status
                """)
                statuses = cursor.fetchall()

                if statuses:
                    print("\nРаспределение по статусам:")
                    headers = ['Статус', 'Количество']
                    rows = [[s['status'], s['count']] for s in statuses]
                    print(tabulate(rows, headers=headers, tablefmt="grid"))

                # Последние отзывы
                cursor.execute(f"""
                    SELECT id, name, service, rating, date, status 
                    FROM {reviews_table} 
                    ORDER BY date DESC 
                    LIMIT 5
                """)
                latest = cursor.fetchall()

                if latest:
                    print("\nПоследние добавленные отзывы:")
                    headers = ['ID', 'Имя', 'Услуга', 'Рейтинг', 'Дата', 'Статус']
                    rows = [[l['id'], l['name'], l['service'], l['rating'], l['date'], l['status']] for l in latest]
                    print(tabulate(rows, headers=headers, tablefmt="grid"))

    except mysql.connector.Error as e:
        print(f"Ошибка при работе с MySQL: {e}")
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()
            print("\nСоединение с MySQL закрыто.")

if __name__ == "__main__":
    print("=" * 80)
    print("ПРОСМОТР ДАННЫХ В БАЗЕ ОТЗЫВОВ")
    print("=" * 80)

    fetch_and_display_data()