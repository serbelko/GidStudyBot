import os
import time

import requests
from dotenv import load_dotenv

def get_get_gpt_info(subject, class_int, description, theme, hard, time_lesson, tests, homework):
    load_dotenv()
    folder_id = os.getenv("YANDEX_FOLDER_ID")
    api_key = os.getenv("YANDEX_API_KEY")
    gpt_model = 'yandexgpt-lite'

    system_prompt = """
    Создай подробный план урока, строго соблюдая следующие требования и структуру.

    Важные условия:
    1. Не используй никакого форматирования (никаких звёздочек, жирного шрифта, подчёркиваний, и т.д.). Текст должен быть полностью "чистым".
    2. Если данные пользователя явно не соответствуют учебной программе (например, он просит что-то неадекватное), укажи на несоответствие и не придумывай сам план урока.
    3. Учитывай все параметры:
    - Предмет (название)
    - Класс (или уровень обучения)
    - Тема урока
    - Личные пожелания учителя (учитывай их в приоритете)
    - Сложность (базовый или продвинутый уровень)
    - Время урока в минутах
    - Необходимость тестирования (True/False)
    - Наличие домашнего задания (True/False)

    Базовая структура урока, если учитель не предложил свою:
    1. Введение:
    - Постановка целей урока и краткий обзор темы
    - Мотивация учащихся: объяснение важности темы
    2. Основная часть:
    - Детальное изложение материала, примеры
    - Демонстрации, визуальные материалы, интерактивные методы
    - Промежуточные проверки понимания
    3. Практическая работа:
    - Упражнения для закрепления
    - Время и формат заданий
    4. Заключение:
    - Обобщение ключевых моментов
    - Ответы на вопросы
    - Обратная связь и рефлексия
    - Домашнее задание (если необходимо)
    5. Дополнительные элементы (при необходимости):
    - Использование мультимедиа
    - Тестирование и критерии оценки
    - Рекомендации для самостоятельного изучения

    Добавь элементы, которые сделают урок интересным (геймификация, нестандартные формы работы). Если часть данных неадекватна или не имеет отношения к уроку, просто сообщи об этом и не придумывай план на эту часть.
    Помни: никаких символов форматирования и разметки.

    """

    user_prompt = f"""
    Пожелания пользователя:
    - Предмет: {subject}
    - Класс: {class_int}
    - Тема урока: {theme}
    - Личные пожелания: {description}
    - Сложность: {hard}
    - Время урока: {time_lesson} минут
    - Тестирование: {tests}
    - Домашнее задание: {homework}

    Если здесь встречаются неадекватные или несвязанные с образованием требования, просто укажи на их несоответствие, не выдумывая план. В остальном прошу составить подробный план урока по вышеприведённой структуре, не применяя никакого форматирования (без звёздочек и прочих элементов).
    """

    body = {
        'modelUri': f'gpt://{folder_id}/{gpt_model}',
        'completionOptions': {'stream': False, 'temperature': 0.9, 'maxTokens': 2000},
        'messages': [
            {'role': 'system', 'text': system_prompt},
            {'role': 'user', 'text': user_prompt},
        ],
    }
    url = 'https://llm.api.cloud.yandex.net/foundationModels/v1/completionAsync'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Api-Key {api_key}'
    }

    response = requests.post(url, headers=headers, json=body)
    operation_id = response.json().get('id')

    url = f"https://llm.api.cloud.yandex.net:443/operations/{operation_id}"
    headers = {"Authorization": f"Api-Key {api_key}"}

    while True:
        response = requests.get(url, headers=headers)
        done = response.json()["done"]
        if done:
            break
        time.sleep(2)

    data = response.json()
    answer = data['response']['alternatives'][0]['message']['text']

    return answer
