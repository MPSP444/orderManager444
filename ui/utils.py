# ui/utils.py

from PyQt5.QtWidgets import QMessageBox
from ui.windows.kanban_styles import MESSAGE_BOX_STYLES, MESSAGE_BOX_STYLE_TEMPLATE


def show_styled_message_box(parent, title, message, type='info', buttons=None):
    """
    Показывает стилизованное окно сообщения

    Args:
        parent: Родительский виджет
        title: Заголовок окна
        message: Текст сообщения
        type: Тип сообщения ('info', 'success', 'warning')
        buttons: Кнопки QMessageBox.StandardButtons
    """
    msg_box = QMessageBox(parent)
    msg_box.setWindowTitle(title)
    msg_box.setText(message)

    # Устанавливаем иконку в зависимости от типа
    if type == 'success':
        msg_box.setIcon(QMessageBox.Information)
    elif type == 'warning':
        msg_box.setIcon(QMessageBox.Warning)
    else:
        msg_box.setIcon(QMessageBox.Question)

    # Устанавливаем кнопки
    if buttons:
        msg_box.setStandardButtons(buttons)

    # Применяем стиль
    style = MESSAGE_BOX_STYLES[type]
    msg_box.setStyleSheet(MESSAGE_BOX_STYLE_TEMPLATE.format(
        background=style['background'],
        border=style['border'],
        button_bg=style['button_bg'],
        button_hover=style['button_hover']
    ))

    return msg_box