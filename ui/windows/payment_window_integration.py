from PyQt5.QtWidgets import QMenu, QPushButton
from ui.windows.path_manager import PathManagerDialog
from ui.windows.excel_manager import ExcelManager
from datetime import datetime


def integrate_path_manager_to_payment_window(payment_window):
    """
    Интегрирует функциональность менеджера путей в окно оплаты
    """
    # Создаем кнопку для настройки путей
    settings_btn = QPushButton("⚙️ Настройки")

    # Создаем меню для кнопки
    settings_menu = QMenu(payment_window)

    # Действие для управления путями
    path_action = settings_menu.addAction("📁 Управление путями")
    path_action.triggered.connect(lambda: show_path_manager(payment_window))

    # Действие для тестирования подключения к Excel
    test_excel_action = settings_menu.addAction("🔄 Проверить Excel")
    test_excel_action.triggered.connect(lambda: test_excel_connection(payment_window))

    # Устанавливаем меню для кнопки
    settings_btn.setMenu(settings_menu)

    # Добавляем кнопку в интерфейс окна оплаты
    # Предполагаем, что у окна оплаты есть buttons_layout
    if hasattr(payment_window, 'buttons_layout'):
        payment_window.buttons_layout.addWidget(settings_btn)
    else:
        # Если нет buttons_layout, добавляем в любой доступный layout
        for attr_name in dir(payment_window):
            attr = getattr(payment_window, attr_name)
            if attr_name.endswith('_layout') and hasattr(attr, 'addWidget'):
                attr.addWidget(settings_btn)
                break


def show_path_manager(parent):
    """
    Показывает диалог управления путями
    """
    dialog = PathManagerDialog(parent)
    dialog.exec_()


def test_excel_connection(parent):
    """
    Проверяет подключение к Excel
    """
    from PyQt5.QtWidgets import QMessageBox
    from path_manager import PathManager

    path_manager = PathManager()
    excel_path = path_manager.get_path('payment_excel')

    if not excel_path:
        QMessageBox.warning(
            parent,
            "Предупреждение",
            "Путь к Excel-файлу платежей не указан.\n"
            "Пожалуйста, укажите путь в настройках."
        )
        return

    excel_manager = ExcelManager(parent)
    success, message = excel_manager.test_excel_connection(excel_path)

    if success:
        QMessageBox.information(parent, "Успех", message)
    else:
        QMessageBox.warning(parent, "Ошибка", message)


def add_excel_record_after_payment(payment_window, order):
    """
    Добавляет запись в Excel после успешного внесения платежа

    Аргументы:
    payment_window - экземпляр окна оплаты
    order - объект заказа, для которого внесена оплата
    """
    try:
        # Получаем сумму оплаты из поля ввода
        payment_amount = float(payment_window.payment_input.text())

        # Создаем менеджер для работы с Excel
        excel_manager = ExcelManager(payment_window)

        # Подготавливаем данные для записи
        payment_data = {
            'date': datetime.now(),
            'client': order.fio,
            'service': order.service,
            'amount': payment_amount
        }

        # Добавляем запись в Excel
        excel_manager.add_payment_to_excel(payment_data)

    except Exception as e:
        from PyQt5.QtWidgets import QMessageBox
        QMessageBox.warning(
            payment_window,
            "Предупреждение",
            f"Ошибка при добавлении записи в Excel: {str(e)}"
        )

# Функция для модификации существующего метода save_payment в классе PaymentWindow
def modify_save_payment_method(payment_window):
    """
    Модифицирует метод save_payment класса PaymentWindow для добавления
    функциональности записи в Excel после успешной оплаты
    """
    # Сохраняем ссылку на оригинальный метод
    original_save_payment = payment_window.save_payment

    # Определяем новую функцию с дополнительной логикой
    def new_save_payment():
        # Вызываем оригинальный метод
        result = original_save_payment()

        # Если оплата была успешно внесена
        if result and hasattr(payment_window, 'current_data'):
            # Получаем текущий заказ
            order_id = payment_window.current_data.get('id')

            with payment_window.db_manager.session_scope() as session:
                from core.database import Order
                order = session.query(Order).get(order_id)

                if order:
                    # Добавляем запись в Excel
                    add_excel_record_after_payment(payment_window, order)

        return result

    # Заменяем оригинальный метод новым
    payment_window.save_payment = new_save_payment