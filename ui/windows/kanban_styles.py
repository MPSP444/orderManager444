# kanban_styles.py

# Цвета для разных статусов
STATUS_COLORS = {
    'new': '#2196F3',  # Синий
    'in_progress': '#2196F3',  # Синий
    'waiting': '#DC2626',  # Красный
    'completed': '#059669',  # Зеленый
    'canceled': '#DC2626'  # Красный
}

# kanban_styles.py

# Цвета для делового стиля
BUSINESS_COLORS = {
    'background': '#F8F9FA',
    'border': '#DEE2E6',
    'text': '#212529',
    'accent': '#0D6EFD',
    'secondary_text': '#6C757D',
    'progress_bar': '#0D6EFD',
    'progress_background': '#E9ECEF'
}

# Цвета статусов в деловом стиле
CARD_BACKGROUNDS = {
    'Новый': '#F8F9FA',          # Светло-серый
    'В работе': '#E9ECEF',       # Серый
    'В ожидании оплаты': '#E2E6EA', # Серо-синий
    'Выполнен': '#D8E3F8',       # Светло-синий
    'Отказ': '#F1F3F5'           # Светло-серый
}

# Стили для карточки заказа
CARD_STYLES = {
    'frame': """
        QFrame {
            background-color: var(--background-color);
            border: 1px solid #DEE2E6;
            border-radius: 4px;
        }
        QFrame:hover {
            border: 1px solid #0D6EFD;
        }
    """,

    'header': """
        background-color: #F8F9FA;
        border-bottom: 1px solid #DEE2E6;
        padding: 8px;
        border-top-left-radius: 4px;
        border-top-right-radius: 4px;
    """,

    'name_label': """
        color: #212529;
        font-size: 13px;
        font-weight: bold;
        padding: 0px 4px;
    """,

    'order_number': """
        color: #6C757D;
        font-size: 12px;
        font-weight: normal;
        font-family: 'Consolas', monospace;
    """,

    'service_label': """
        color: #495057;
        font-size: 12px;
        padding: 4px;
        border-bottom: 1px solid #DEE2E6;
    """,

    'progress_bar': """
        QProgressBar {
            background-color: #E9ECEF;
            border: none;
            border-radius: 2px;
            text-align: center;
            font-size: 11px;
            font-weight: bold;
            color: #212529;
            margin: 4px;
        }
        QProgressBar::chunk {
            border-radius: 2px;
        }
    """,

    'cost_label': """
        color: #495057;
        font-size: 12px;
        font-family: 'Consolas', monospace;
        padding: 2px 4px;
    """,

    'deadline_label': """
        color: #6C757D;
        font-size: 11px;
        padding: 2px 4px;
        border-top: 1px solid #DEE2E6;
    """,
    'bottom_panel': """
        background-color: #F8F9FA;
        border-top: 1px solid #DEE2E6;
        border-bottom-left-radius: 4px;
        border-bottom-right-radius: 4px;
    """,

    'bottom_text': """
        color: #6C757D;
        font-size: 11px;
        font-family: 'Consolas', monospace;
    """
}

# Цвета для прогресс-бара в зависимости от процента оплаты
PROGRESS_BAR_COLORS = {
    'complete': '#4CAF50',  # Яркий зеленый для 100%
    'high': '#FF9800',      # Яркий оранжевый для >= 75%
    'normal': '#2196F3',    # Яркий синий для >= 50%
    'low': '#F44336'        # Яркий красный для < 50%
}



# Стили для колонки канбана
COLUMN_STYLES = {
    'main': """
        QWidget {
            background-color: #F9FAFB;
            border-radius: 8px;
        }
    """,

    'header': """
        QWidget {
            background-color: white;
            border-radius: 8px;
        }
    """,

    'title': """
        color: #1F2937;
        font-size: 14px;
        font-weight: 500;
    """,

    'counter': """
        color: white;
        font-weight: 500;
        padding: 4px 12px;
        border-radius: 4px;
        font-size: 12px;
    """,

    'scroll_area': """
        QScrollArea {
            border: none;
            background-color: transparent;
        }
        QScrollBar:vertical {
            border: none;
            background-color: #F3F4F6;
            width: 6px;
            margin: 0px;
        }
        QScrollBar::handle:vertical {
            background-color: #D1D5DB;
            border-radius: 3px;
            min-height: 20px;
        }
        QScrollBar::handle:vertical:hover {
            background-color: #9CA3AF;
        }
        QScrollBar::add-line:vertical, 
        QScrollBar::sub-line:vertical {
            height: 0px;
        }
    """
}

# Стили для канбан-доски
BOARD_STYLES = {
    'main': """
        QWidget {
            background-color: #F9FAFB;
        }
    """
}

# Маппинг статусов для колонок
STATUS_MAPPING = {
    'Новые': 'Новый',
    'В работе': 'В работе',
    'Ожидают оплаты': 'В ожидании оплаты',
    'Выполнены': 'Выполнен',
    'Отменены': 'Отказ'
}

# Размеры элементов
SIZES = {
    'card_width': 280,
    'card_height': 140,
    'column_width': 320,
    'header_height': 40,
    'progress_bar_height': 20
}
# Цвета для диалоговых окон в соответствии со статусами
DIALOG_BACKGROUNDS = {
    'Новый': '#E3F2FD',  # Светло-синий
    'В работе': '#FFF3E0',  # Светло-оранжевый
    'В ожидании оплаты': '#FFEBEE',  # Светло-красный
    'Выполнен': '#E8F5E9',  # Светло-зеленый
    'Отказ': '#FFEBEE'  # Светло-красный
}

# Стили для диалоговых окон
DIALOG_STYLES = """
    QDialog {{
        background-color: {bg_color};
        border: 1px solid #ddd;
        border-radius: 8px;
    }}

    QLabel {{
        color: #333333;
        font-size: 13px;
    }}

    QPushButton {{
        background-color: {button_color};
        color: white;
        border: none;
        padding: 8px 16px;
        border-radius: 4px;
        font-weight: bold;
    }}

    QPushButton:hover {{
        background-color: {button_hover};
    }}

    QComboBox {{
        background-color: white;
        border: 1px solid #ddd;
        border-radius: 4px;
        padding: 5px;
    }}

    QLineEdit {{
        background-color: white;
        border: 1px solid #ddd;
        border-radius: 4px;
        padding: 5px;
    }}
"""

# Цвета кнопок для разных статусов
BUTTON_COLORS = {
    'Новый': {'normal': '#2196F3', 'hover': '#1976D2'},
    'В работе': {'normal': '#FF9800', 'hover': '#F57C00'},
    'В ожидании оплаты': {'normal': '#F44336', 'hover': '#D32F2F'},
    'Выполнен': {'normal': '#4CAF50', 'hover': '#388E3C'},
    'Отказ': {'normal': '#F44336', 'hover': '#D32F2F'}
}

# Стили для QMessageBox
MESSAGE_BOX_STYLES = {
    'info': {
        'background': '#E3F2FD',  # Светло-синий
        'border': '#2196F3',  # Синий
        'icon_color': '#2196F3',  # Синий
        'button_bg': '#2196F3',  # Синий
        'button_hover': '#1976D2'  # Темно-синий
    },
    'success': {
        'background': '#E8F5E9',  # Светло-зеленый
        'border': '#4CAF50',  # Зеленый
        'icon_color': '#4CAF50',  # Зеленый
        'button_bg': '#4CAF50',  # Зеленый
        'button_hover': '#388E3C'  # Темно-зеленый
    },
    'warning': {
        'background': '#FFF3E0',  # Светло-оранжевый
        'border': '#FF9800',  # Оранжевый
        'icon_color': '#FF9800',  # Оранжевый
        'button_bg': '#FF9800',  # Оранжевый
        'button_hover': '#F57C00'  # Темно-оранжевый
    }
}

# Шаблон стиля для QMessageBox
MESSAGE_BOX_STYLE_TEMPLATE = """
    QMessageBox {{
        background-color: {background};
        border: 2px solid {border};
        border-radius: 8px;
    }}

    QMessageBox QLabel {{
        color: #333333;
        font-size: 13px;
        min-width: 300px;
        padding: 10px;
    }}

    QMessageBox QPushButton {{
        background-color: {button_bg};
        color: white;
        border: none;
        border-radius: 4px;
        padding: 8px 16px;
        min-width: 100px;
        font-weight: bold;
    }}

    QMessageBox QPushButton:hover {{
        background-color: {button_hover};
    }}
"""