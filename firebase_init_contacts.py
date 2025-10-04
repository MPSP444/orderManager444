#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Скрипт для инициализации и заполнения тестовыми данными
коллекции контактов в Firebase.
"""

import requests
import json
from datetime import datetime, timedelta
import random
import uuid
import time

# URL вашей базы данных Firebase
FIREBASE_URL = "https://ordermanagerreviews-default-rtdb.europe-west1.firebasedatabase.app"

# Имена для тестовых контактов
TEST_NAMES = [
    "Иванов Иван", "Петрова Мария", "Сидоров Алексей", "Смирнова Елена",
    "Кузнецов Дмитрий", "Васильева Анна", "Попов Сергей", "Соколова Ольга",
    "Михайлов Андрей", "Федорова Наталья", "Морозов Павел", "Волкова Татьяна"
]

# Темы сообщений
MESSAGE_SUBJECTS = [
    "Вопрос о стоимости услуг",
    "Консультация по курсовой работе",
    "Запрос на расчет стоимости",
    "Нужна помощь с дипломной работой",
    "Интересует разработка сайта",
    "Вопрос о сроках выполнения",
    "Запрос коммерческого предложения",
    "Хочу заказать контрольную работу",
    "Нужна помощь с программированием",
    "Консультация по экономике"
]

# Статусы
STATUSES = ["new", "in_progress", "completed"]


def generate_phone():
    """Генерирует случайный номер телефона"""
    return f"+7{random.randint(900, 999)}{random.randint(1000000, 9999999)}"


def generate_email(name):
    """Генерирует email на основе имени"""
    transliteration = {
        'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'e',
        'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
        'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
        'ф': 'f', 'х': 'h', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'sch', 'ъ': '',
        'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya'
    }

    name_parts = name.lower().split()
    if len(name_parts) >= 2:
        first_name = ''.join([transliteration.get(c, c) for c in name_parts[0]])
        last_name = ''.join([transliteration.get(c, c) for c in name_parts[1]])
        email = f"{first_name}.{last_name}@{random.choice(['gmail.com', 'mail.ru', 'yandex.ru', 'outlook.com'])}"
        return email
    else:
        return f"user_{random.randint(1000, 9999)}@example.com"


def generate_message():
    """Генерирует текст сообщения"""
    templates = [
        "Здравствуйте! {subject}. Можете подсказать стоимость и сроки выполнения?",
        "Добрый день. {subject}. Хотел(а) бы узнать подробности о ваших услугах.",
        "Приветствую! Меня интересует {subject}. Можно узнать условия сотрудничества?",
        "Здравствуйте. {subject}. Подскажите, пожалуйста, можете ли вы помочь с этим вопросом?",
        "Добрый вечер! {subject}. Сколько будет стоить и как быстро можно выполнить?"
    ]

    subject = random.choice(MESSAGE_SUBJECTS).lower()
    template = random.choice(templates)
    message = template.format(subject=subject)

    # Добавляем детали
    details = [
        " Мне нужно сдать работу до {deadline}.",
        " Тема касается {topic}.",
        " Объем примерно {pages} страниц.",
        " Можно ли выполнить за {days} дней?",
        " Бюджет около {budget} рублей.",
        ""
    ]

    # Добавляем 1-3 случайных детали
    num_details = random.randint(1, 3)
    selected_details = random.sample(details, num_details)

    for detail in selected_details:
        if "{deadline}" in detail:
            deadline_date = (datetime.now() + timedelta(days=random.randint(5, 30))).strftime("%d.%m.%Y")
            message += detail.format(deadline=deadline_date)
        elif "{topic}" in detail:
            topics = ["экономики", "менеджмента", "программирования", "маркетинга", "статистики", "психологии"]
            message += detail.format(topic=random.choice(topics))
        elif "{pages}" in detail:
            message += detail.format(pages=random.randint(10, 100))
        elif "{days}" in detail:
            message += detail.format(days=random.randint(3, 14))
        elif "{budget}" in detail:
            message += detail.format(budget=random.randint(1000, 10000))
        else:
            message += detail

    message += " Буду ждать вашего ответа!"
    return message


def generate_random_contact(days_ago=None):
    """Генерирует случайный контакт"""
    name = random.choice(TEST_NAMES)

    # Генерируем дату
    if days_ago is None:
        days_ago = random.randint(0, 30)
    contact_date = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")
    # Добавляем случайное время
    contact_time = f"{random.randint(8, 23):02d}:{random.randint(0, 59):02d}:{random.randint(0, 59):02d}"

    # Определяем статус на основе даты (более старые имеют больше шансов быть завершенными)
    status_weights = {
        "new": max(0, 10 - days_ago // 3),  # Чем старше, тем меньше шансов быть новым
        "in_progress": 5,
        "completed": min(10, days_ago // 2)  # Чем старше, тем больше шансов быть завершенным
    }

    statuses = list(status_weights.keys())
    weights = list(status_weights.values())
    status = random.choices(statuses, weights=weights, k=1)[0]

    # Для завершенных и обработанных заявок можем добавить ответ
    response = ""
    if status in ["in_progress", "completed"]:
        responses = [
            "Здравствуйте! Благодарим за обращение. Стоимость наших услуг начинается от 1500 рублей. Готовы обсудить детали по телефону.",
            "Добрый день! Мы можем помочь с вашим запросом. Примерная стоимость составит 2000-4000 рублей в зависимости от сложности. Перезвоним вам в ближайшее время.",
            "Приветствую! Спасибо за интерес к нашим услугам. Предлагаем созвониться для обсуждения деталей и составления точной сметы.",
            "Здравствуйте! Готовы взяться за вашу работу. Для расчета точной стоимости нам нужны дополнительные детали. Можем ли мы связаться с вами?"
        ]
        response = random.choice(responses)

    contact = {
        "name": name,
        "email": generate_email(name),
        "phone": generate_phone(),
        "message": generate_message(),
        "date": contact_date,
        "time": contact_time,
        "status": status
    }

    # Добавляем ответ, если он есть
    if response:
        contact["response"] = response

    # Добавляем заметки для некоторых контактов
    if random.random() < 0.3:  # 30% контактов имеют заметки
        notes = [
            "Клиент звонил повторно, уточнял сроки",
            "Запросил дополнительную скидку, обещали рассмотреть",
            "Перенаправлен к специалисту по экономике",
            "Постоянный клиент, ранее делал заказы",
            "Особое внимание: сжатые сроки выполнения",
            "Рекомендован нашим партнером"
        ]
        contact["notes"] = random.choice(notes)

    # Добавляем время последнего напоминания для некоторых контактов
    if status == "in_progress" and random.random() < 0.5:  # 50% контактов в обработке имеют напоминание
        reminder_days_ago = random.randint(1, min(5, days_ago))
        last_reminder = (datetime.now() - timedelta(days=reminder_days_ago)).timestamp()
        contact["last_reminder"] = last_reminder

    # Добавляем флаг просмотра
    contact["viewed"] = status != "new"

    return contact


def create_contacts_collection():
    """Создает и заполняет коллекцию контактов тестовыми данными"""
    print("Начинаем инициализацию коллекции контактов...")

    # Создаем тестовые контакты
    contacts = {}

    # Создаем 20 случайных контактов с различными датами
    for i in range(20):
        # Контакты распределены по последним 30 дням
        days_ago = int((i / 20) * 30)
        contact_id = str(uuid.uuid4())
        contacts[contact_id] = generate_random_contact(days_ago=days_ago)

    # Добавляем специальные тестовые случаи

    # 1. Новая заявка от сегодня
    today_contact_id = str(uuid.uuid4())
    today_contact = generate_random_contact(days_ago=0)
    today_contact["status"] = "new"
    today_contact["viewed"] = False
    contacts[today_contact_id] = today_contact

    # 2. Срочная заявка в обработке
    urgent_contact_id = str(uuid.uuid4())
    urgent_contact = generate_random_contact(days_ago=1)
    urgent_contact["status"] = "in_progress"
    urgent_contact["notes"] = "СРОЧНО! Клиент ожидает ответа в ближайшее время"
    contacts[urgent_contact_id] = urgent_contact

    # 3. Заявка с множеством деталей
    detailed_contact_id = str(uuid.uuid4())
    detailed_contact = generate_random_contact(days_ago=3)
    detailed_contact["message"] = """
    Здравствуйте! Меня интересует выполнение дипломной работы по экономике на тему "Оптимизация логистических процессов на предприятии".

    Детали:
    - Объем работы: 80-100 страниц
    - Срок сдачи: 25.05.2025
    - Требуется практическая часть с анализом реального предприятия
    - Необходимо 3 главы: теоретическая, аналитическая и проектная
    - Требуется презентация и речь для защиты

    У меня есть методические указания и пример похожей работы. Могу предоставить доступ к данным предприятия.

    Какая примерная стоимость такой работы и возможные сроки выполнения?

    Спасибо!
    """
    contacts[detailed_contact_id] = detailed_contact

    # Отправляем данные в Firebase
    url = f"{FIREBASE_URL}/contacts.json"
    response = requests.put(url, json=contacts)

    if response.status_code == 200:
        print(f"Успешно создано {len(contacts)} тестовых контактов в Firebase")
        print(f"URL коллекции: {FIREBASE_URL}/contacts.json")
        return True
    else:
        print(f"Ошибка при создании коллекции: {response.status_code}")
        print(response.text)
        return False


def clear_contacts_collection():
    """Очищает коллекцию контактов"""
    print("Очистка коллекции контактов...")

    url = f"{FIREBASE_URL}/contacts.json"
    response = requests.delete(url)

    if response.status_code == 200:
        print("Коллекция контактов успешно очищена")
        return True
    else:
        print(f"Ошибка при очистке коллекции: {response.status_code}")
        print(response.text)
        return False


def check_contacts_collection():
    """Проверяет существование коллекции контактов"""
    url = f"{FIREBASE_URL}/contacts.json"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        if data:
            count = len(data) if isinstance(data, dict) else 0
            print(f"Коллекция контактов уже существует и содержит {count} записей")
            return True
        else:
            print("Коллекция контактов существует, но пуста")
            return False
    else:
        print(f"Ошибка при проверке коллекции: {response.status_code}")
        print(response.text)
        return False


def main():
    """Основная функция скрипта"""
    print("Инициализация тестовых данных для модуля контактов")
    print(f"Firebase URL: {FIREBASE_URL}")

    # Проверяем существование коллекции
    collection_exists = check_contacts_collection()

    if collection_exists:
        answer = input("Коллекция уже существует. Очистить и пересоздать? (y/n): ")
        if answer.lower() == 'y':
            clear_contacts_collection()
            time.sleep(1)  # Небольшая пауза перед созданием
            create_contacts_collection()
        else:
            print("Операция отменена.")
    else:
        create_contacts_collection()


if __name__ == "__main__":
    main()