# kanban_styles.py
# -*- coding: utf-8 -*-
"""
Этот модуль содержит обновлённые определения стилей для канбан-доски.
В данном варианте переработаны отступы, размеры и типографика для достижения
идеального делового оформления: заголовок остаётся строго в рамках 305px,
шрифты и цвета настроены для лучшей читаемости и визуальной иерархии.
"""

# Базовые цвета статусов (более сдержанные)
STATUS_COLORS = {
    'Новый': '#1976D2',            # Более тёмный синий
    'В работе': '#F57C00',         # Более тёмный оранжевый
    'В ожидании оплаты': '#D32F2F',  # Более тёмный красный
    'Выполнен': '#388E3C',         # Более тёмкий зеленый
    'Отказ': '#616161'             # Более тёмкий серый
}

# Расширенные стили статусов
STATUS_STYLES = {
    'Новый': {
        'bg': '#FFFFFF',
        'header_bg': '#FAFAFA',
        'border': '#90CAF9',  # <== Убедитесь, что этот ключ есть!
        'count_bg': '#1976D2',
        'title_color': '#2A2A2A',
        'title_font': '"Georgia", serif',
        'title_size': '18px',
        'title_weight': '600',
        'amount_bg': '#F8F8F8'
    },
    'В работе': {
        'bg': '#FFFFFF',
        'header_bg': '#FFF8E1',
        'border': '#FFB74D',  # <== Должен быть!
        'count_bg': '#F57C00',
        'title_color': '#2A2A2A',
        'title_font': '"Times New Roman", serif',
        'title_size': '20px',
        'title_weight': '700',
        'amount_bg': '#F8F8F8'
    },
    'В ожидании оплаты': {
        'bg': '#FFFFFF',
        'header_bg': '#FFEBEE',
        'border': '#EF9A9A',  # <== Должен быть!
        'count_bg': '#D32F2F',
        'title_color': '#2A2A2A',
        'title_font': '"Georgia", serif',
        'title_size': '18px',
        'title_weight': '600',
        'amount_bg': '#F8F8F8'
    },
    'Выполнен': {
        'bg': '#FFFFFF',
        'header_bg': '#E8F5E9',
        'border': '#A5D6A7',  # <== Должен быть!
        'count_bg': '#388E3C',
        'title_color': '#2A2A2A',
        'title_font': '"Verdana", sans-serif',
        'title_size': '18px',
        'title_weight': '600',
        'amount_bg': '#F8F8F8'
    },
    'Отказ': {
        'bg': '#FFFFFF',
        'header_bg': '#ECEFF1',
        'border': '#B0BEC5',  # <== Должен быть!
        'count_bg': '#616161',
        'title_color': '#2A2A2A',
        'title_font': '"Georgia", serif',
        'title_size': '18px',
        'title_weight': '600',
        'amount_bg': '#F8F8F8'
    }
}


CARDS_LIST_STYLE = """
QListView {{
    background-color: transparent;
    border: none;
    padding: 4px 2px;
    margin: 0px;
}}

QScrollBar:vertical {{
    width: 8px;
    background: transparent;
    margin: 0px;
}}

QScrollBar::handle:vertical {{
    background: {border};
    border-radius: 4px;
    min-height: 20px;
}}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {{
    height: 0px;
}}

QScrollBar::add-page:vertical,
QScrollBar::sub-page:vertical {{
    background: none;
}}
"""

# ==================== Стили для карточки ====================

CARD_STYLE = """
QFrame {{
    background-color: white;
    border: 1px solid {border};
    border-radius: 6px;
    margin: 3px;
    padding: 6px;
}}

QLabel {{
    color: #333333;
    font-size: 14px;
    margin: 4px 0px;
}}

QLabel#title {{
    color: {title_color};
    font-size: 15px;
    font-weight: bold;
    padding-bottom: 6px;
}}

QLabel#group_label,
QLabel#service_label {{
    margin-right: 6px;
    color: #555555;
}}

QLabel#group_value,
QLabel#service_value {{
    font-weight: 500;
}}

QLabel#amount {{
    color: #444444;
    font-weight: bold;
    font-size: 15px;
    padding-top: 4px;
}}

QLabel#status {{
    color: {count_bg};
    font-size: 13px;
    font-weight: 500;
    padding-top: 4px;
}}
"""
