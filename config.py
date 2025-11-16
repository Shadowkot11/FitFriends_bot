import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_CHAT_ID = os.getenv('ADMIN_CHAT_ID')

# Настройки AI
OPENROUTER_API_KEY = "free"  # Бесплатный AI API

# База знаний упражнений
EXERCISE_LIBRARY = {
    'home': {
        'beginner': [
            {'name': 'Отжимания от пола', 'sets': '3x10', 'gif': 'https://media.giphy.com/media/l0HlNF9TtMfL9MsvW/giphy.gif'},
            {'name': 'Приседания', 'sets': '3x15', 'gif': 'https://media.giphy.com/media/3o7TKSha51ATTx9KzC/giphy.gif'},
            {'name': 'Планка', 'sets': '3x30сек', 'gif': 'https://media.giphy.com/media/xT5LMJm930guk5Nlfi/giphy.gif'},
            {'name': 'Выпады', 'sets': '3x10', 'gif': 'https://media.giphy.com/media/l0HlKrLJSv9X22LbW/giphy.gif'},
            {'name': 'Скручивания', 'sets': '3x15', 'gif': 'https://media.giphy.com/media/26uf759LlDftqZKYk/giphy.gif'}
        ]
    }
}

# База питания
NUTRITION_PLANS = {
    'weight_loss': {
        'breakfast': 'Овсянка с ягодами (300 ккал)',
        'lunch': 'Курица с гречкой и овощами (400 ккал)',
        'dinner': 'Рыба на пару с салатом (350 ккал)',
        'snacks': 'Яблоко, творог (200 ккал)'
    },
    'muscle_gain': {
        'breakfast': 'Омлет из 3 яиц + тосты (500 ккал)',
        'lunch': 'Говядина с рисом (600 ккал)',
        'dinner': 'Творог с орехами (400 ккал)',
        'snacks': 'Протеин, банан (300 ккал)'
    }
}