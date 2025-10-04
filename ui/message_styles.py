# ui/message_styles.py

# Основные цвета
COLORS = {
    'primary': '#1E88E5',       # Основной синий
    'success': '#43A047',       # Зеленый для успешных операций
    'warning': '#FB8C00',       # Оранжевый для предупреждений
    'error': '#E53935',         # Красный для ошибок
    'text': '#2C3E50',          # Цвет текста
    'border': '#E0E0E0'         # Цвет границ
}

# Основной стиль для всех MessageBox
MESSAGE_BOX_STYLE = f"""
    QMessageBox {{
        background-color: white;
        border: 2px solid {COLORS['primary']};
        border-radius: 8px;
        min-width: 320px;
    }}

    QMessageBox QLabel {{
        color: {COLORS['text']};
        font-size: 13px;
        font-family: 'Segoe UI', Arial;
        padding: 10px;
        min-width: 280px;
    }}

    QMessageBox QPushButton {{
        background-color: {COLORS['primary']};
        color: white;
        border: none;
        border-radius: 4px;
        padding: 8px 20px;
        min-width: 100px;
        font-weight: bold;
        font-size: 13px;
        margin: 5px;
    }}

    QMessageBox QPushButton:hover {{
        background-color: #1976D2;
    }}

    QMessageBox QPushButton:pressed {{
        background-color: #1565C0;
    }}
"""