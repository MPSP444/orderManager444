from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QLineEdit, QGroupBox, QTextEdit,
                             QScrollArea, QFrame,QFileDialog, QSplitter,QMessageBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor
from core.database import init_database, Order
from sqlalchemy import func
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from datetime import datetime
from PyQt5.QtWidgets import QFileDialog

class ClientAnalyticsTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.session = init_database()
        self.initUI()

    def initUI(self):
        """Инициализация интерфейса"""
        layout = QVBoxLayout(self)

        # Верхняя панель с поиском
        search_layout = QHBoxLayout()

        # Поле поиска
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Поиск клиента по ФИО или телефону...")
        self.search_input.setMinimumWidth(300)
        self.search_input.textChanged.connect(self.search_client)
        self.search_input.setStyleSheet("""
            QLineEdit {
                padding: 8px 15px;
                border: 1px solid #ddd;
                border-radius: 20px;
                background: white;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 2px solid #2196F3;
            }
        """)
        search_layout.addWidget(self.search_input)

        layout.addLayout(search_layout)

        # Основной контент
        content_splitter = QSplitter(Qt.Horizontal)

        # Левая панель - список клиентов
        clients_group = QGroupBox("Список клиентов")
        clients_layout = QVBoxLayout(clients_group)

        self.clients_scroll = QScrollArea()
        self.clients_scroll.setWidgetResizable(True)
        self.clients_scroll.setMinimumWidth(300)

        self.clients_widget = QWidget()
        self.clients_layout = QVBoxLayout(self.clients_widget)
        self.clients_scroll.setWidget(self.clients_widget)

        clients_layout.addWidget(self.clients_scroll)
        content_splitter.addWidget(clients_group)

        # Правая панель - информация о клиенте
        client_info = QWidget()
        info_layout = QVBoxLayout(client_info)

        # Основная информация
        main_info = QGroupBox("Основная информация")
        main_info_layout = QVBoxLayout(main_info)
        self.client_name_label = QLabel("Выберите клиента")
        self.client_name_label.setFont(QFont("Arial", 14, QFont.Bold))
        main_info_layout.addWidget(self.client_name_label)

        self.client_details = QLabel()
        main_info_layout.addWidget(self.client_details)
        info_layout.addWidget(main_info)

        # Статистика
        stats_group = QGroupBox("Статистика заказов")
        stats_layout = QVBoxLayout(stats_group)
        self.stats_label = QLabel()
        stats_layout.addWidget(self.stats_label)
        info_layout.addWidget(stats_group)

        # Рекомендации
        recommendations_group = QGroupBox("Рекомендации")
        recommendations_layout = QVBoxLayout(recommendations_group)
        self.recommendations_label = QLabel()
        recommendations_layout.addWidget(self.recommendations_label)
        info_layout.addWidget(recommendations_group)

        # Кнопки действий
        actions_layout = QHBoxLayout()

        new_order_btn = QPushButton("📝 Новый заказ")
        new_order_btn.clicked.connect(self.create_new_order)

        send_offer_btn = QPushButton("📤 Отправить предложение")
        send_offer_btn.clicked.connect(self.send_offer)

        print_info_btn = QPushButton("🖨️ Печать информации")
        print_info_btn.clicked.connect(self.print_client_info)

        actions_layout.addWidget(new_order_btn)
        actions_layout.addWidget(send_offer_btn)
        actions_layout.addWidget(print_info_btn)

        info_layout.addLayout(actions_layout)

        content_splitter.addWidget(client_info)
        content_splitter.setStretchFactor(1, 2)  # Правая часть шире

        layout.addWidget(content_splitter)

        # Загружаем список клиентов
        self.load_clients()

        # Применяем стили
        self.setStyleSheet("""
            QGroupBox {
                border: 1px solid #ddd;
                border-radius: 6px;
                margin-top: 10px;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)

    def load_clients(self):
        """Загрузка списка клиентов"""
        # Очищаем текущий список
        while self.clients_layout.count():
            child = self.clients_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        try:
            # Получаем клиентов и их статистику
            clients = self.session.query(
                Order.fio,
                func.count(Order.id).label('total_orders'),
                func.sum(Order.cost).label('total_cost')
            ).group_by(Order.fio).order_by(func.count(Order.id).desc()).all()

            # Создаем карточку для каждого клиента
            for client in clients:
                client_card = self.create_client_card(
                    name=client.fio,
                    orders=client.total_orders,
                    total=client.total_cost or 0
                )
                self.clients_layout.addWidget(client_card)

            # Добавляем растягивающийся элемент
            self.clients_layout.addStretch()

        except Exception as e:
            print(f"Ошибка при загрузке клиентов: {e}")

    def create_client_card(self, name, orders, total):
        """Создание карточки клиента"""
        card = QFrame()
        card.setFrameShape(QFrame.StyledPanel)
        card.setStyleSheet("""
            QFrame {
                border: 1px solid #ddd;
                border-radius: 4px;
                background: white;
                padding: 10px;
                margin: 5px;
            }
            QFrame:hover {
                background: #f5f5f5;
                border: 1px solid #2196F3;
            }
        """)

        layout = QVBoxLayout(card)

        # Имя клиента
        name_label = QLabel(name)
        name_label.setFont(QFont("Arial", 10, QFont.Bold))
        layout.addWidget(name_label)

        # Статистика
        stats = QLabel(f"Заказов: {orders} | Сумма: {total:,.2f}₽")
        stats.setStyleSheet("color: #666;")
        layout.addWidget(stats)

        # Делаем карточку кликабельной
        card.mousePressEvent = lambda e: self.show_client_details(name)

        return card

    def show_client_details(self, client_name):
        """Показ детальной информации о клиенте"""
        try:
            # Получаем данные клиента
            client_data = self.session.query(
                Order.fio,
                func.count(Order.id).label('total_orders'),
                func.sum(Order.cost).label('total_cost'),
                func.avg(Order.cost).label('avg_cost'),
                func.sum(Order.remaining_amount).label('debt')
            ).filter(Order.fio == client_name).group_by(Order.fio).first()

            if client_data:
                # Обновляем основную информацию
                self.client_name_label.setText(client_data.fio)

                # Статистика
                stats_text = f"""
                <h3>Общая статистика:</h3>
                • Всего заказов: {client_data.total_orders}<br>
                • Общая сумма: {client_data.total_cost:,.2f}₽<br>
                • Средний чек: {client_data.avg_cost:,.2f}₽<br>
                • Текущий долг: {client_data.debt:,.2f}₽
                """
                self.stats_label.setText(stats_text)

                # Рекомендации
                recommendations = []

                # Рекомендация по скидке
                if client_data.total_orders >= 5:
                    recommendations.append("• Рекомендуемая скидка: 15%")
                elif client_data.total_orders >= 3:
                    recommendations.append("• Рекомендуемая скидка: 10%")
                else:
                    recommendations.append("• Рекомендуемая скидка: 5%")

                # Рекомендация по оплате
                if client_data.debt > 0:
                    recommendations.append("• Рекомендуется внести остаток оплаты")
                else:
                    recommendations.append("• Платежная дисциплина: отличная")

                # Рекомендация по заказам
                if client_data.total_orders > 0:
                    recommendations.append("• Рекомендуется предложить постоянное сотрудничество")

                recommendations_text = f"""
                <h3>Рекомендации:</h3>
                {"<br>".join(recommendations)}
                """
                self.recommendations_label.setText(recommendations_text)

        except Exception as e:
            print(f"Ошибка при показе информации о клиенте: {e}")
            QMessageBox.critical(self, "Ошибка", f"Ошибка при показе информации: {str(e)}")

    def search_client(self, text):
        """Поиск клиента"""
        try:
            # Если поле поиска пустое, показываем всех клиентов
            if not text.strip():
                self.load_clients()
                return

            search_text = text.lower().strip()

            # Разные варианты поиска
            if any(char.isdigit() for char in search_text):
                # Если в строке поиска есть цифры - ищем по телефону
                clean_search = ''.join(filter(str.isdigit, search_text))

                clients = self.session.query(
                    Order.fio,
                    Order.phone,
                    func.count(Order.id).label('total_orders'),
                    func.sum(Order.cost).label('total_cost')
                ).group_by(Order.fio, Order.phone).all()

                # Фильтруем по телефону
                filtered_clients = [
                    client for client in clients
                    if (client.phone and
                        clean_search in ''.join(filter(str.isdigit, client.phone)))
                ]
            else:
                # Поиск по ФИО
                search_words = search_text.split()
                clients = self.session.query(
                    Order.fio,
                    Order.phone,
                    func.count(Order.id).label('total_orders'),
                    func.sum(Order.cost).label('total_cost')
                ).group_by(Order.fio, Order.phone).all()

                # Фильтруем по всем словам из поиска
                filtered_clients = [
                    client for client in clients
                    if all(word in client.fio.lower() for word in search_words)
                ]

            # Обновляем UI
            while self.clients_layout.count():
                child = self.clients_layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()

            for client in filtered_clients:
                client_card = self.create_client_card(
                    name=client.fio,
                    orders=client.total_orders,
                    total=client.total_cost or 0
                )
                self.clients_layout.addWidget(client_card)

            self.clients_layout.addStretch()

            if not filtered_clients:
                # Добавляем сообщение, если ничего не найдено
                no_results = QLabel("Ничего не найдено")
                no_results.setStyleSheet("color: #666; padding: 20px;")
                self.clients_layout.addWidget(no_results)

        except Exception as e:
            print(f"Ошибка при поиске клиентов: {e}")
            QMessageBox.critical(self, "Ошибка", f"Ошибка при поиске клиентов: {str(e)}")

    def create_new_order(self):
        """Создание нового заказа для клиента"""
        if not self.client_name_label.text() or self.client_name_label.text() == "Выберите клиента":
            QMessageBox.warning(self, "Предупреждение", "Сначала выберите клиента")
            return

        try:
            from ui.windows.new_order_window import NewOrderWindow
            dialog = NewOrderWindow(self)
            # Предзаполняем ФИО клиента
            dialog.fio_input.setText(self.client_name_label.text())
            dialog.exec_()

            # После создания заказа обновляем информацию
            self.show_client_details(self.client_name_label.text())
            self.load_clients()  # Обновляем список клиентов

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при создании заказа: {str(e)}")

    def send_offer(self):
        """Отправка предложения клиенту"""
        if not self.client_name_label.text() or self.client_name_label.text() == "Выберите клиента":
            QMessageBox.warning(self, "Предупреждение", "Сначала выберите клиента")
            return

        try:
            # Получаем данные клиента
            client = self.session.query(Order).filter(
                Order.fio == self.client_name_label.text()
            ).first()

            if not client or not client.phone:
                QMessageBox.warning(self, "Предупреждение", "У клиента не указан номер телефона")
                return

            # Формируем текст предложения
            offer_text = self.generate_offer_text(client)

            # Открываем WhatsApp
            from urllib.parse import quote
            import webbrowser

            whatsapp_url = f"https://wa.me/{client.phone.replace('+', '').replace('-', '').replace(' ', '')}?text={quote(offer_text)}"
            webbrowser.open(whatsapp_url)

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при отправке предложения: {str(e)}")

    def generate_offer_text(self, client):
        """Генерация текста предложения"""
        # Получаем статистику клиента
        stats = self.session.query(
            func.count(Order.id).label('total_orders'),
            func.sum(Order.cost).label('total_cost')
        ).filter(Order.fio == client.fio).first()

        # Формируем рекомендуемую скидку
        if stats.total_orders >= 5:
            discount = "15%"
        elif stats.total_orders >= 3:
            discount = "10%"
        else:
            discount = "5%"

        # Формируем текст предложения
        text = f"""Здравствуйте, {client.fio}!

Спасибо, что выбираете нас! 🙏🙂

Для вас, как для нашего {'постоянного' if stats.total_orders > 1 else 'нового'} клиента:
• Персональная скидка: {discount}
• Гибкие условия оплаты
• Индивидуальный подход

Готовы обсудить ваш следующий заказ! 

С уважением,
Команда MPSP"""

        return text

    def generate_recommendations(self, client_data):
        """Генерация рекомендаций для клиента"""
        recommendations = []

        # Рекомендация по скидке
        if client_data.total_orders >= 5:
            recommendations.append("Рекомендуемая скидка: 15%")
        elif client_data.total_orders >= 3:
            recommendations.append("Рекомендуемая скидка: 10%")
        else:
            recommendations.append("Рекомендуемая скидка: 5%")

        # Рекомендация по оплате
        if client_data.debt > 0:
            recommendations.append("Рекомендуется внести остаток оплаты")
        else:
            recommendations.append("Платежная дисциплина: отличная")

        # Рекомендация по заказам
        if client_data.total_orders > 0:
            recommendations.append("Рекомендуется: предложить постоянное сотрудничество")

        return recommendations

    def print_client_info(self):
        """Печать информации о клиенте"""
        if not self.client_name_label.text() or self.client_name_label.text() == "Выберите клиента":
            QMessageBox.warning(self, "Предупреждение", "Сначала выберите клиента")
            return

        try:
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import mm
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.ttfonts import TTFont

            # Создаем имя файла
            file_name = f"Клиент_{self.client_name_label.text()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Сохранить отчет",
                file_name,
                "PDF files (*.pdf)"
            )

            if file_path:
                # Регистрируем шрифт DejaVu (поддерживает кириллицу)
                try:
                    pdfmetrics.registerFont(TTFont('DejaVu', 'C:\\Windows\\Fonts\\DejaVuSans.ttf'))
                except:
                    try:
                        pdfmetrics.registerFont(TTFont('DejaVu', '/usr/share/fonts/TTF/DejaVuSans.ttf'))
                    except:
                        # Если не нашли DejaVu, пробуем Arial
                        try:
                            pdfmetrics.registerFont(TTFont('DejaVu', 'C:\\Windows\\Fonts\\arial.ttf'))
                        except:
                            raise Exception("Не удалось найти подходящий шрифт с поддержкой кириллицы")

                # Создаем документ
                doc = SimpleDocTemplate(
                    file_path,
                    pagesize=A4,
                    rightMargin=20 * mm,
                    leftMargin=20 * mm,
                    topMargin=20 * mm,
                    bottomMargin=20 * mm,
                    encoding='utf-8'
                )

                # Создаем стили с нашим шрифтом
                styles = getSampleStyleSheet()
                title_style = ParagraphStyle(
                    'CustomTitle',
                    parent=styles['Heading1'],
                    fontSize=16,
                    fontName='DejaVu',
                    spaceAfter=30,
                    encoding='utf-8'
                )
                normal_style = ParagraphStyle(
                    'CustomNormal',
                    parent=styles['Normal'],
                    fontSize=12,
                    fontName='DejaVu',
                    encoding='utf-8'
                )

                # Получаем данные клиента
                client_data = self.session.query(
                    Order.fio,
                    func.count(Order.id).label('total_orders'),
                    func.sum(Order.cost).label('total_cost'),
                    func.avg(Order.cost).label('avg_cost'),
                    func.sum(Order.remaining_amount).label('debt')
                ).filter(Order.fio == self.client_name_label.text()).group_by(Order.fio).first()

                elements = []

                # Заголовок
                elements.append(Paragraph(f"Информация о клиенте: {client_data.fio}", title_style))
                elements.append(Spacer(1, 20))

                # Основная информация
                elements.append(Paragraph("ОБЩАЯ СТАТИСТИКА", title_style))
                elements.append(Paragraph(f"• Всего заказов: {client_data.total_orders}", normal_style))
                elements.append(Paragraph(f"• Общая сумма заказов: {client_data.total_cost:,.2f}₽", normal_style))
                elements.append(Paragraph(f"• Средний чек: {client_data.avg_cost:,.2f}₽", normal_style))
                elements.append(Paragraph(f"• Текущая задолженность: {client_data.debt:,.2f}₽", normal_style))
                elements.append(Spacer(1, 20))

                # Рекомендации
                elements.append(Paragraph("РЕКОМЕНДАЦИИ", title_style))
                recommendations = self.generate_recommendations(client_data)
                for rec in recommendations:
                    elements.append(Paragraph(f"• {rec}", normal_style))

                # Создаем документ
                doc.build(elements)
                QMessageBox.information(self, "Успех", "Отчет успешно создан!")

        except Exception as e:
            print(f"Ошибка при создании отчета: {e}")  # Для отладки
            QMessageBox.critical(self, "Ошибка", f"Ошибка при создании отчета: {str(e)}")
