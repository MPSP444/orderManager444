# ui/message_utils.py

from PyQt5.QtWidgets import QMessageBox
from .message_styles import MESSAGE_BOX_STYLE


def show_message(parent, title, message, icon=QMessageBox.Information, buttons=QMessageBox.Ok):
    """
    Универсальная функция для показа сообщений

    Args:
        parent: Родительский виджет
        title: Заголовок окна
        message: Текст сообщения
        icon: Иконка (QMessageBox.Information, QMessageBox.Warning, QMessageBox.Critical, QMessageBox.Question)
        buttons: Кнопки (QMessageBox.Ok, QMessageBox.Yes | QMessageBox.No, и т.д.)
    """
    msg = QMessageBox(parent)
    msg.setWindowTitle(title)
    msg.setText(message)
    msg.setIcon(icon)
    msg.setStandardButtons(buttons)
    msg.setStyleSheet(MESSAGE_BOX_STYLE)
    return msg.exec_()


def show_question(parent, title, message):
    """Показ вопроса с кнопками Да/Нет"""
    return show_message(
        parent,
        title,
        message,
        icon=QMessageBox.Question,
        buttons=QMessageBox.Yes | QMessageBox.No
    ) == QMessageBox.Yes


def show_info(parent, title, message):
    """Показ информационного сообщения"""
    show_message(parent, title, message, QMessageBox.Information)


def show_warning(parent, title, message):
    """Показ предупреждения"""
    show_message(parent, title, message, QMessageBox.Warning)


def show_error(parent, title, message):
    """Показ сообщения об ошибке"""
    show_message(parent, title, message, QMessageBox.Critical)