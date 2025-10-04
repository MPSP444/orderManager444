# ui/dialog_styles.py

# Основной цвет для всех диалоговых окон
DIALOG_PRIMARY_COLOR = '#2196F3'  # Красивый синий
DIALOG_HOVER_COLOR = '#1976D2'  # Темно-синий для hover эффектов
DIALOG_STYLE = """
    QDialog {
        background-color: white;
    }
    QLabel {
        color: #333;
    }
    QPushButton {
        color: white;
        background-color: #2196F3;
        border: none;
        padding: 8px 16px;
        border-radius: 4px;
    }
    QPushButton:hover {
        background-color: #1976D2;
    }
    QLineEdit, QTextEdit {
        border: 1px solid #ddd;
        padding: 8px;
        border-radius: 4px;
        color: #333;
    }
"""
# Стили для QMessageBox
MESSAGEBOX_STYLE = f"""
    QMessageBox {{
        background-color: white;
        border: 2px solid {DIALOG_PRIMARY_COLOR};
        border-radius: 8px;
        min-width: 300px;
    }}

    QMessageBox QLabel {{
        color: #333333;
        font-size: 13px;
        padding: 10px;
        font-weight: normal;
    }}

    QMessageBox QPushButton {{
        background-color: {DIALOG_PRIMARY_COLOR};
        color: white;
        border: none;
        border-radius: 4px;
        padding: 8px 16px;
        min-width: 100px;
        font-weight: bold;
        font-size: 13px;
    }}

    QMessageBox QPushButton:hover {{
        background-color: {DIALOG_HOVER_COLOR};
    }}
"""

# Стили для других диалоговых окон (например, окна оплаты, изменения статуса и т.д.)
DIALOG_WINDOW_STYLE = f"""
    QDialog {{
        background-color: white;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
    }}

    QLabel {{
        color: #333333;
        font-size: 13px;
    }}

    QPushButton {{
        background-color: {DIALOG_PRIMARY_COLOR};
        color: white;
        border: none;
        border-radius: 4px;
        padding: 8px 16px;
        min-width: 100px;
        font-weight: bold;
        font-size: 13px;
    }}

    QPushButton:hover {{
        background-color: {DIALOG_HOVER_COLOR};
    }}

    QLineEdit, QComboBox {{
        border: 1px solid #e0e0e0;
        border-radius: 4px;
        padding: 8px;
        background-color: white;
    }}

    QLineEdit:focus, QComboBox:focus {{
        border: 2px solid {DIALOG_PRIMARY_COLOR};
    }}
"""

# Для окон с подтверждением действий
CONFIRMATION_DIALOG_STYLE = f"""
    QDialog {{
        background-color: white;
        border: 2px solid {DIALOG_PRIMARY_COLOR};
        border-radius: 8px;
        min-width: 400px;
    }}

    QLabel {{
        color: #333333;
        font-size: 14px;
        padding: 15px;
    }}

    QPushButton {{
        background-color: {DIALOG_PRIMARY_COLOR};
        color: white;
        border: none;
        border-radius: 4px;
        padding: 10px 20px;
        min-width: 120px;
        font-weight: bold;
        font-size: 13px;
        margin: 5px;
    }}

    QPushButton:hover {{
        background-color: {DIALOG_HOVER_COLOR};
    }}
"""