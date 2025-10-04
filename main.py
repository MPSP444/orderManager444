import sys
import os
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtGui import QFont
from ui.windows import MainWindow
from ui.login_window import LoginWindow
from database.db import init_admin
from sqlalchemy import create_engine, text


# Функция для добавления колонки review_token
def add_review_token_column():
    try:
        engine = create_engine('sqlite:///orders.db')
        with engine.connect() as conn:
            # Проверяем, существует ли уже колонка
            result = conn.execute(text("PRAGMA table_info(orders)"))
            columns = [row[1] for row in result.fetchall()]

            if 'review_token' not in columns:
                conn.execute(text("ALTER TABLE orders ADD COLUMN review_token VARCHAR(100)"))
                conn.commit()
                print("Колонка review_token успешно добавлена")
            else:
                print("Колонка review_token уже существует")
    except Exception as e:
        print(f"Ошибка при проверке/добавлении колонки: {e}")


# Функция для запуска менеджера отзывов как отдельного приложения
def run_reviews_manager():
    """Запуск менеджера отзывов как отдельного приложения"""
    try:
        # Создаем новый экземпляр QApplication для менеджера отзывов
        app = QApplication(sys.argv)

        # Настраиваем шрифт
        font = QFont("Arial", 10)
        app.setFont(font)

        # Импортируем и запускаем окно управления отзывами
        from reviews_manager.ui.reviews_window import ReviewsManagementWindow
        window = ReviewsManagementWindow()
        window.show()

        # Запускаем новый цикл событий
        app.exec_()
    except Exception as e:
        print(f"Ошибка при запуске менеджера отзывов: {e}")
        QMessageBox.critical(None, "Ошибка", f"Не удалось запустить менеджер отзывов: {str(e)}")


# Добавляем путь к корневой директории проекта в PYTHONPATH
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)
sys.path.append(current_dir)  # Добавляем текущую директорию для доступа к модулю reviews_manager


def main():
    try:
        print("Запуск приложения")
        # Создаем приложение
        app = QApplication(sys.argv)

        print("Настройка шрифта")
        # Настраиваем шрифт по умолчанию
        font = QFont("Arial", 10)
        app.setFont(font)

        print("Инициализация админа")
        # Инициализируем админский аккаунт
        init_admin()

        print("Добавление колонки review_token")
        # Добавляем колонку review_token, если она не существует
        add_review_token_column()

        print("Создание окна авторизации")
        # Создаем и показываем окно авторизации
        login_window = LoginWindow()
        login_window.show()

        print("Ожидание результата авторизации")
        # Если авторизация успешна, показываем главное окно
        if login_window.exec_() == LoginWindow.Accepted:
            print("Авторизация успешна, создание главного окна")
            try:
                # Создаем и показываем главное окно
                window = MainWindow()
                print("Показ главного окна")
                window.show()

                # Запускаем цикл событий приложения
                print("Запуск цикла событий")
                return app.exec_()
            except Exception as e:
                print(f"Ошибка при создании главного окна: {e}")
                import traceback
                traceback.print_exc()
                QMessageBox.critical(None, "Критическая ошибка", f"Ошибка при создании главного окна: {e}")
                return 1
        else:
            print("Авторизация отменена")
            return 0
    except Exception as e:
        print(f"Ошибка в main(): {e}")
        import traceback
        traceback.print_exc()
        return 1


# Точка входа для запуска менеджера отзывов как отдельного процесса
def run_reviews_manager_entry():
    # Предотвращаем повторную инициализацию QApplication
    # если запускаем как подпроцесс из основного приложения
    if not QApplication.instance():
        app = QApplication(sys.argv)

    # Запускаем менеджер отзывов
    from reviews_manager.main import run_gui
    run_gui()


if __name__ == '__main__':
    # Проверяем аргументы командной строки
    if len(sys.argv) > 1 and sys.argv[1] == "--reviews-manager":
        # Запускаем менеджер отзывов как отдельное приложение
        run_reviews_manager_entry()
    else:
        # Запускаем основное приложение
        sys.exit(main())