# themes.py

LIGHT_THEME = """
/* Основное окно */
QMainWindow {
    background-color: #ffffff;
}

/* Основные элементы */
QWidget {
    font-family: 'Segoe UI', Arial;
    font-size: 13px;
}

/* Кнопки */
QPushButton {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                stop:0 #3498db, stop:1 #2980b9);
    color: white;
    border: none;
    padding: 8px 16px;
    border-radius: 6px;
    font-weight: 600;
    margin: 3px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

QPushButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                stop:0 #2980b9, stop:1 #2472a4);
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
}

QPushButton:pressed {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                stop:0 #2472a4, stop:1 #2980b9);
    padding: 9px 15px 7px 17px;
}

/* Таблица */
QTableWidget {
    background-color: white;
    border: none;
    border-radius: 10px;
    gridline-color: #ecf0f1;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
}

QTableWidget::item {
    padding: 12px;
    border-bottom: 1px solid #ecf0f1;
    transition: background-color 0.2s;
}

QTableWidget::item:selected {
    background-color: #3498db22;
    color: #2c3e50;
    border-left: 3px solid #3498db;
}

QHeaderView::section {
    background-color: #f8f9fa;
    padding: 15px;
    border: none;
    border-bottom: 2px solid #3498db;
    font-weight: bold;
    color: #2c3e50;
    font-size: 13px;
}

/* Вкладки с современным дизайном */
QTabWidget::pane {
    border: none;
    background: white;
    border-radius: 10px;
    margin-top: -1px;
}

QTabBar::tab {
    background-color: transparent;
    padding: 12px 20px;
    border: none;
    margin-right: 4px;
    color: #7f8c8d;
    font-weight: 500;
}

QTabBar::tab:selected {
    color: #3498db;
    border-bottom: 2px solid #3498db;
}

QTabBar::tab:hover:!selected {
    color: #2980b9;
    background-color: rgba(52, 152, 219, 0.1);
    border-radius: 4px;
}

/* Поля поиска с эффектами */
QLineEdit {
    padding: 10px 15px;
    border: 2px solid #ecf0f1;
    border-radius: 8px;
    background-color: white;
    font-size: 13px;
    transition: all 0.3s;
}

QLineEdit:focus {
    border: 2px solid #3498db;
    background-color: #f8f9fa;
    box-shadow: 0 0 10px rgba(52, 152, 219, 0.2);
}

/* Выпадающие списки */
QComboBox {
    padding: 10px 15px;
    border: 2px solid #ecf0f1;
    border-radius: 8px;
    background-color: white;
    min-width: 150px;
    font-size: 13px;
}

QComboBox:hover {
    border-color: #3498db;
    background-color: #f8f9fa;
}

QComboBox::drop-down {
    border: none;
    width: 30px;
}

QComboBox::down-arrow {
    image: url(down_arrow.png);
    width: 12px;
    height: 12px;
}
"""

DARK_THEME = """
/* Темная тема */
QMainWindow {
    background-color: #1a1a1a;
}

QWidget {
    color: #ffffff;
    font-family: 'Segoe UI', Arial;
    font-size: 13px;
}

QPushButton {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                stop:0 #2980b9, stop:1 #2472a4);
    color: white;
    border: none;
    padding: 8px 16px;
    border-radius: 6px;
    font-weight: 600;
}

QTableWidget {
    background-color: #2c2c2c;
    border: none;
    gridline-color: #3c3c3c;
    color: #ffffff;
}

QTableWidget::item {
    padding: 12px;
    border-bottom: 1px solid #3c3c3c;
}

QTableWidget::item:selected {
    background-color: #2980b9;
    color: white;
}

QHeaderView::section {
    background-color: #2c2c2c;
    color: #ffffff;
    border-bottom: 2px solid #2980b9;
}

/* Остальные стили для темной темы... */
"""

# themes.py

# Добавляем новые темы к существующим LIGHT_THEME и DARK_THEME

BLUE_GRADIENT_THEME = """
QMainWindow {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                              stop:0 #EBF5FB, stop:1 #D6EAF8);
}

QPushButton {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                              stop:0 #3498db, stop:1 #2980b9);
    color: white;
    border: none;
    padding: 6px 12px;
    border-radius: 5px;
    font-weight: 600;
}

QPushButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                              stop:0 #2980b9, stop:1 #2472a4);
}

QTableWidget {
    background-color: rgba(255, 255, 255, 0.9);
    border: none;
    border-radius: 8px;
}

QTableWidget::item {
    padding: 8px;
    border-bottom: 1px solid #E8F6FF;
}

QTableWidget::item:selected {
    background-color: #3498db22;
    color: #2c3e50;
    border-left: 3px solid #3498db;
}

QLineEdit {
    padding: 6px 10px;
    border: 2px solid #BDC3C7;
    border-radius: 5px;
    background: white;
}

QLineEdit:focus {
    border: 2px solid #3498DB;
    background: #F8FBFD;
}
"""

ELEGANT_PURPLE_THEME = """
QMainWindow {
    background-color: #FFFFFF;
}

QPushButton {
    background-color: #9B59B6;
    color: white;
    border: none;
    padding: 6px 12px;
    border-radius: 5px;
    font-weight: 600;
}

QPushButton:hover {
    background-color: #8E44AD;
    box-shadow: 0 2px 5px rgba(0,0,0,0.2);
}

QTableWidget {
    background-color: white;
    border: 1px solid #E8E8E8;
    border-radius: 8px;
}

QTableWidget::item {
    padding: 8px;
    border-bottom: 1px solid #F4F4F4;
}

QTableWidget::item:selected {
    background-color: #9B59B622;
    color: #2C3E50;
    border-left: 3px solid #9B59B6;
}

QHeaderView::section {
    background-color: #F8F9FA;
    padding: 8px;
    border: none;
    border-bottom: 2px solid #9B59B6;
}
"""

MODERN_GREEN_THEME = """
QMainWindow {
    background-color: #FAFAFA;
}

QPushButton {
    background-color: #27AE60;
    color: white;
    border: none;
    padding: 6px 12px;
    border-radius: 5px;
    font-weight: 600;
}

QPushButton:hover {
    background-color: #219A52;
}

QTableWidget {
    background-color: white;
    border: none;
    border-radius: 8px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.05);
}

QTableWidget::item {
    padding: 8px;
    border-bottom: 1px solid #F0F0F0;
}

QTableWidget::item:selected {
    background-color: #27AE6022;
    color: #2C3E50;
    border-left: 3px solid #27AE60;
}

QLineEdit {
    padding: 6px 10px;
    border: 2px solid #E0E0E0;
    border-radius: 5px;
    background: white;
}

QLineEdit:focus {
    border: 2px solid #27AE60;
    background: #F9FDF9;
}
"""

SOFT_ORANGE_THEME = """
QMainWindow {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                              stop:0 #FFF8F3, stop:1 #FFF1E6);
}

QPushButton {
    background-color: #E67E22;
    color: white;
    border: none;
    padding: 6px 12px;
    border-radius: 5px;
    font-weight: 600;
}

QPushButton:hover {
    background-color: #D35400;
}

QTableWidget {
    background-color: rgba(255, 255, 255, 0.95);
    border: none;
    border-radius: 8px;
}

QTableWidget::item {
    padding: 8px;
    border-bottom: 1px solid #FFE6D6;
}

QHeaderView::section {
    background-color: #FFF8F3;
    padding: 8px;
    border: none;
    border-bottom: 2px solid #E67E22;
}
"""

MINIMAL_GRAY_THEME = """
QMainWindow {
    background-color: #F5F5F5;
}

QPushButton {
    background-color: #607D8B;
    color: white;
    border: none;
    padding: 6px 12px;
    border-radius: 5px;
    font-weight: 600;
}

QPushButton:hover {
    background-color: #546E7A;
}

QTableWidget {
    background-color: white;
    border: 1px solid #E0E0E0;
    border-radius: 8px;
}

QTableWidget::item {
    padding: 8px;
    border-bottom: 1px solid #F5F5F5;
}

QLineEdit {
    padding: 6px 10px;
    border: 2px solid #E0E0E0;
    border-radius: 5px;
    background: white;
}

QLineEdit:focus {
    border: 2px solid #607D8B;
    background: #FAFAFA;
}
"""
# themes.py

MINIMAL_ENHANCED_THEME = """
QMainWindow {
    background-color: #F5F5F5;
}

/* Кнопки */
QPushButton {
    background-color: #607D8B;
    color: white;
    border: none;
    padding: 6px 12px;
    border-radius: 5px;
    font-weight: 600;
}

QPushButton:hover {
    background-color: #546E7A;
}

/* Таблица */
QTableWidget {
    background-color: white;
    border: 1px solid #E0E0E0;
    border-radius: 8px;
    color: #333333;  /* Темный цвет текста */
}

QTableWidget::item {
    padding: 8px;
    border-bottom: 1px solid #F5F5F5;
    color: #333333;  /* Убеждаемся, что текст всегда темный */
}

QTableWidget::item:selected {
    background-color: #E8F5E8;  /* Очень светлый зеленый */
    color: #333333;  /* Текст остается темным при выделении */
    border-left: 3px solid #81C784;  /* Мягкий зеленый индикатор */
}

/* Заголовки таблицы */
QHeaderView::section {
    background-color: #F8F9FA;
    padding: 8px;
    border: none;
    border-bottom: 2px solid #607D8B;
    color: #333333;
    font-weight: bold;
}

/* Поля ввода */
QLineEdit {
    padding: 6px 10px;
    border: 2px solid #E0E0E0;
    border-radius: 5px;
    background: white;
    color: #333333;
}

QLineEdit:focus {
    border: 2px solid #81C784;
    background: #F9FDF9;
}

/* Выпадающие списки */
QComboBox {
    padding: 6px 10px;
    border: 2px solid #E0E0E0;
    border-radius: 5px;
    background: white;
    color: #333333;
}

QComboBox:hover {
    border: 2px solid #81C784;
}
"""