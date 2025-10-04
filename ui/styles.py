# styles.py

MAIN_THEME = """
/* Основное окно */
QMainWindow {
    background-color: #f5f5f5;
}

/* Кнопки */
QPushButton {
    background-color: #2196F3;
    color: white;
    border: none;
    padding: 5px 15px;
    border-radius: 4px;
    font-weight: bold;
    margin: 2px;
}

QPushButton:hover {
    background-color: #1976D2;
}

QPushButton:pressed {
    background-color: #0D47A1;
}

/* Таблица */
QTableWidget {
    background-color: white;
    border: 1px solid #ddd;
    border-radius: 4px;
    gridline-color: #f0f0f0;
}

QTableWidget::item {
    padding: 5px;
}

QTableWidget::item:selected {
    background-color: #e3f2fd;
    color: black;
}

QHeaderView::section {
    background-color: #f5f5f5;
    padding: 8px;
    border: none;
    border-right: 1px solid #ddd;
    border-bottom: 1px solid #ddd;
    font-weight: bold;
}

/* Вкладки */
QTabWidget::pane {
    border: 1px solid #ddd;
    border-radius: 4px;
    background: white;
}

QTabBar::tab {
    background-color: #f5f5f5;
    padding: 8px 15px;
    border: 1px solid #ddd;
    border-bottom: none;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
}

QTabBar::tab:selected {
    background-color: white;
    border-bottom: 2px solid #2196F3;
}

/* Поля поиска */
QLineEdit {
    padding: 5px;
    border: 1px solid #ddd;
    border-radius: 4px;
    background-color: white;
}

QLineEdit:focus {
    border: 2px solid #2196F3;
}

/* Выпадающие списки */
QComboBox {
    padding: 5px;
    border: 1px solid #ddd;
    border-radius: 4px;
    background-color: white;
}

QComboBox:hover {
    border: 1px solid #2196F3;
}

QComboBox::drop-down {
    border: none;
}

/* Полосы прокрутки */
QScrollBar:vertical {
    border: none;
    background: #f5f5f5;
    width: 10px;
    margin: 0px;
}

QScrollBar::handle:vertical {
    background: #90a4ae;
    border-radius: 5px;
}

QScrollBar::handle:vertical:hover {
    background: #78909c;
}
"""

# Стили для тулбара
TOOLBAR_STYLES = """
QToolBar {
    background-color: white;
    border-bottom: 1px solid #ddd;
    spacing: 5px;
    padding: 5px;
}

QToolBar QPushButton {
    background-color: transparent;
    color: #424242;
    border: none;
    padding: 5px;
    border-radius: 4px;
}

QToolBar QPushButton:hover {
    background-color: #f5f5f5;
}

QToolBar QPushButton:pressed {
    background-color: #e0e0e0;
}
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