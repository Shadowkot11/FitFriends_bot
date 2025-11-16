import aiohttp
import json
import random
from datetime import datetime

class AIFitnessEngine:
    def __init__(self):
        self.api_url = "https://openrouter.ai/api/v1/chat/completions"
        self.api_key = "free"  # Бесплатный доступ

    async def generate_ai_response(self, user_message, conversation_history):
        """Генерирует AI-ответ на вопрос пользователя"""

        system_prompt = """
        Ты - профессиональный AI-фитнес тренер и нутрициолог. Ты помогаешь с:
        - Персональными тренировками
        - Планами питания
        - Мотивацией и поддержкой
        - Ответами на спортивные вопросы

        Будь дружелюбным, профессиональным и мотивирующим. Давай конкретные советы.
        """

        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "model": "mistralai/mistral-7b-instruct:free",
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        *conversation_history[-10:],  # Последние 10 сообщений
                        {"role": "user", "content": user_message}
                    ],
                    "max_tokens": 500
                }

                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }

                async with session.post(self.api_url, json=payload, headers=headers) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result['choices'][0]['message']['content']
                    else:
                        return self.get_fallback_response(user_message)

        except Exception as e:
            return self.get_fallback_response(user_message)

    def get_fallback_response(self, user_message):
        """Резервные ответы если AI не работает"""
        fallback_responses = {
            'привет': 'Привет! Я твой AI-фитнес тренер! 🏋️\nЧем могу помочь? Тренировка, питание или совет?',
            'треня': 'Отлично! Сгенерирую для тебя персональную тренировку! 💪',
            'питание': 'Создам идеальный план питания под твои цели! 🥗',
            'мотивация': 'Ты можешь всё! Каждая тренировка приближает к цели! 🔥',
            'как похудеть': 'Советую: 1) Дефицит калорий 2) Силовые тренировки 3) Кардио 4) Белок',
            'как накачаться': 'Фокус на: 1) Прогрессия нагрузок 2) Протеин 3) Восстановление 4) Дисциплина'
        }

        user_message_lower = user_message.lower()
        for key, response in fallback_responses.items():
            if key in user_message_lower:
                return response

        return "Отличный вопрос! Рекомендую тебе индивидуальную программу тренировок и питания. Хочешь, создам её для тебя? 🚀"

    def generate_workout_plan(self, user_data):
        """Генерирует персонализированную тренировку"""
        level = user_data.get('fitness_level', 'beginner')
        goals = user_data.get('goals', 'weight_loss')

        workouts = {
            'weight_loss': {
                'type': 'Жиросжигающая',
                'focus': 'Кардио + Силовая',
                'exercises': [
                    'Приседания 4x15',
                    'Берпи 3x10',
                    'Планка 3x60сек',
                    'Выпады 3x12',
                    'Скакалка 5x1мин'
                ]
            },
            'muscle_gain': {
                'type': 'Мышечная масса',
                'focus': 'Силовая',
                'exercises': [
                    'Приседания 4x8-10',
                    'Отжимания 4x10-12',
                    'Подтягивания 3x6-8',
                    'Ягодичный мостик 4x12',
                    'Планка 3x45сек'
                ]
            }
        }

        workout = workouts.get(goals, workouts['weight_loss'])

        return {
            'date': datetime.now().strftime('%d.%m.%Y'),
            'type': workout['type'],
            'focus': workout['focus'],
            'duration': '35-45 минут',
            'calories': '250-400 ккал',
            'exercises': workout['exercises']
        }

    def generate_nutrition_plan(self, user_data):
        """Генерирует план питания"""
        goals = user_data.get('goals', 'weight_loss')

        plans = {
            'weight_loss': {
                'calories': '1800-2000 ккал',
                'meals': {
                    'breakfast': 'Овсянка с ягодами и протеином',
                    'lunch': 'Куриная грудка с гречкой и овощами',
                    'dinner': 'Рыба на пару с салатом',
                    'snacks': 'Творог, яблоко, орехи'
                }
            },
            'muscle_gain': {
                'calories': '2800-3200 ккал',
                'meals': {
                    'breakfast': 'Омлет из 4 яиц + овсянка',
                    'lunch': 'Говядина с рисом и овощами',
                    'dinner': 'Творог с бананом и орехами',
                    'snacks': 'Протеин, фрукты, йогурт'
                }
            }
        }

        return plans.get(goals, plans['weight_loss'])

ai_engine = AIFitnessEngine()