from PyQt5.QtWidgets import QPushButton
from PyQt5.QtCore import Qt

class OrderButton(QPushButton):
    """Базовый класс для кнопок заказов"""
    def __init__(self, text, shortcut=None, parent=None):
        super().__init__(text, parent)
        if shortcut:
            self.setShortcut(shortcut)
        self.setCursor(Qt.PointingHandCursor)

# Основные действия
class NewOrderButton(OrderButton):
    def __init__(self, parent=None):
        super().__init__("📝 Новый заказ", "Ctrl+L", parent)

class EditOrderButton(OrderButton):
    def __init__(self, parent=None):
        super().__init__("✏️ Редактировать", "Ctrl+R", parent)

class DeleteOrderButton(OrderButton):
    def __init__(self, parent=None):
        super().__init__("❌ Удалить", "Ctrl+U", parent)

class CancelOrderButton(OrderButton):
    def __init__(self, parent=None):
        super().__init__("⛔ Отменить заказ", "Ctrl+O", parent)

class AddPaymentButton(OrderButton):
    def __init__(self, parent=None):
        super().__init__("💰 Внести оплату", "Ctrl+V", parent)

class KanbanBoardButton(OrderButton):
    def __init__(self, parent=None):
        super().__init__("📋 Канбан-доска", parent)

# Информация и анализ
class BasicInfoButton(OrderButton):
    def __init__(self, parent=None):
        super().__init__("ℹ️ Получить информацию", parent)

class DetailedInfoButton(OrderButton):
    def __init__(self, parent=None):
        super().__init__("📊 Подробная информация", "Ctrl+P", parent)

class StatisticsButton(OrderButton):
    def __init__(self, parent=None):
        super().__init__("📈 Статистика", parent)

class PaymentScheduleButton(OrderButton):
    def __init__(self, parent=None):
        super().__init__("💹 График платежей", parent)

class OrderDeadlinesButton(OrderButton):
    def __init__(self, parent=None):
        super().__init__("⏰ Сроки заказов", parent)

class ProfitReportButton(OrderButton):
    def __init__(self, parent=None):
        super().__init__("💰 Отчет о прибыли", parent)

class DebtAnalysisButton(OrderButton):
    def __init__(self, parent=None):
        super().__init__("💸 Анализ задолженностей", parent)

# Дополнительные функции
class OrderHistoryButton(OrderButton):
    def __init__(self, parent=None):
        super().__init__("📜 История заказа", parent)

class TopClientsButton(OrderButton):
    def __init__(self, parent=None):
        super().__init__("🏆 Топ клиенты", parent)

class ServicesAnalysisButton(OrderButton):
    def __init__(self, parent=None):
        super().__init__("📊 Анализ услуг", parent)

class LoyaltySystemButton(OrderButton):
    def __init__(self, parent=None):
        super().__init__("💎 Система лояльности", parent)

class HotkeysButton(OrderButton):
    def __init__(self, parent=None):
        super().__init__("⌨️ Горячие клавиши", parent)
class ImportExcelButton(OrderButton):
    def __init__(self, parent=None):
        super().__init__("📥 Импорт Excel", parent)
class ColumnSettingsButton(OrderButton):
    def __init__(self, parent=None):
        super().__init__("⚙️ Настройка колонок", parent)
# Фильтры
class UniqueClientsButton(OrderButton):
    def __init__(self, parent=None):
        super().__init__("👥 Список клиентов", parent)
class AllClientsButton(OrderButton):
    def __init__(self, parent=None):
        super().__init__("👥 Все клиенты", parent)

class GroupedClientsButton(OrderButton):
    def __init__(self, parent=None):
        super().__init__("👥 Клиенты по ФИО", parent)

class NewOrdersButton(OrderButton):
    def __init__(self, parent=None):
        super().__init__("🆕 Новые", parent)

class InProgressButton(OrderButton):
    def __init__(self, parent=None):
        super().__init__("🔄 В работе", parent)

class PaidOrdersButton(OrderButton):
    def __init__(self, parent=None):
        super().__init__("✅ Оплаченные", parent)

class DebtorsButton(OrderButton):
    def __init__(self, parent=None):
        super().__init__("⚠️ Должники", parent)

class CompletedOrdersButton(OrderButton):
    def __init__(self, parent=None):
        super().__init__("✔️ Выполненные", parent)

class WaitingPaymentButton(OrderButton):
    def __init__(self, parent=None):
        super().__init__("⏳ В ожидании оплаты", parent)

class CanceledOrdersButton(OrderButton):
    def __init__(self, parent=None):
        super().__init__("❌ Отмененные", parent)