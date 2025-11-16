import logging
import asyncio
import random
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters

import config
from database import db
from ai_engine import ai_engine

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('pro_bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class FitFriends_bot:
    def __init__(self, token):
        self.application = Application.builder().token(token).build()
        self.setup_handlers()
        self.sales_automation = SalesAutomation()

    def setup_handlers(self):
        # Команды
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("workout", self.quick_workout))
        self.application.add_handler(CommandHandler("nutrition", self.quick_nutrition))
        self.application.add_handler(CommandHandler("progress", self.show_progress))

        # Кнопки
        self.application.add_handler(CallbackQueryHandler(self.button_handler))

        # Все сообщения (AI чат)
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_ai_chat))

        # Напоминания
        self.application.job_queue.run_repeating(self.send_reminders, interval=3600, first=10)

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user

        # Регистрация пользователя
        db.add_user(user.id, user.username, user.first_name, user.last_name)

        # Авто-воронка: новый лид
        db.update_lead_stage(user.id, 'new')

        welcome_text = f"""
🤖 <b>Добро пожаловать в AI-FITNESS PRO, {user.first_name}!</b>

Я твой персональный <b>AI-тренер, нутрициолог и мотивационный друг</b>!

🎯 <b>Что я умею:</b>
• 🏋️ Создавать персональные тренировки
• 🥗 Составлять планы питания
• 📊 Анализировать прогресс
• 💬 Отвечать на любые вопросы
• 🔔 Напоминать о тренировках
• 🎯 Мотивировать 24/7

🚀 <b>Начни с бесплатного 7-дневного trial!</b>

Выбери действие:
        """

        keyboard = [
            [InlineKeyboardButton("🎯 Пройти опрос (2 мин)", callback_data='start_survey')],
            [InlineKeyboardButton("💪 Быстрая тренировка", callback_data='quick_workout')],
            [InlineKeyboardButton("🥗 План питания", callback_data='nutrition_plan')],
            [InlineKeyboardButton("💬 Задать вопрос AI", callback_data='ai_chat')],
            [InlineKeyboardButton("🔗 Подключить Яндекс Алису", callback_data='connect_alice')],
            [InlineKeyboardButton("💎 Premium доступ", callback_data='premium_offer')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode='HTML')

        # Авто-сообщение через 1 минуту
        context.job_queue.run_once(
            self.send_followup_message,
            60,
            data=user.id,
            name=f"followup_{user.id}"
        )

    async def send_followup_message(self, context: ContextTypes.DEFAULT_TYPE):
        """Авто-сообщение через 1 минуту"""
        user_id = context.job.data

        followup_text = """
💡 <b>Не знаешь с чего начать?</b>

Рекомендую:
1. Пройти быстрый опрос (2 минуты)
2. Получить персональную программу
3. Начать первую тренировку!

Или просто спроси меня о чем угодно! 💬
        """

        keyboard = [
            [InlineKeyboardButton("🎯 Начать опрос", callback_data='start_survey')],
            [InlineKeyboardButton("💬 Спросить AI", callback_data='ai_chat')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        try:
            await context.bot.send_message(
                user_id,
                followup_text,
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
        except Exception as e:
            logger.warning(f"Не удалось отправить followup: {e}")

    async def button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        user_id = query.from_user.id

        if query.data == 'start_survey':
            await self.start_survey(query)
        elif query.data == 'quick_workout':
            await self.send_workout(query)
        elif query.data == 'nutrition_plan':
            await self.send_nutrition(query)
        elif query.data == 'ai_chat':
            await self.start_ai_chat(query)
        elif query.data == 'connect_alice':
            await self.show_alice_connection(query)
        elif query.data == 'premium_offer':
            await self.show_premium_offer(query)
        elif query.data == 'complete_survey':
            await self.complete_survey(query)

    async def start_survey(self, query):
        """Начало опроса для персонализации"""
        survey_text = """
🎯 <b>ДАВАЙ ПОЗНАКОМИМСЯ!</b>

Ответь на 3 быстрых вопроса для персонализации:

1. <b>Какая твоя основная цель?</b>
   • Похудение
   • Набор мышечной массы
   • Поддержание формы
   • Улучшение здоровья

Напиши свой ответ:
        """

        await query.edit_message_text(survey_text, parse_mode='HTML')

        # Сохраняем состояние опроса
        db.update_conversation(query.from_user.id, "start_survey", "goal_question")

    async def send_workout(self, query):
        """Отправляет AI-тренировку"""
        user_id = query.from_user.id
        user_data = db.get_user(user_id)

        # Генерируем тренировку
        workout = ai_engine.generate_workout_plan({
            'fitness_level': user_data[6] if user_data else 'beginner',
            'goals': user_data[5] if user_data else 'weight_loss'
        })

        workout_text = f"""
🏋️ <b>ТВОЯ AI-ТРЕНИРОВКА</b>

📅 <b>Дата:</b> {workout['date']}
🎯 <b>Тип:</b> {workout['type']}
⏱ <b>Время:</b> {workout['duration']}
🔥 <b>Калории:</b> {workout['calories']}

<b>Упражнения:</b>
"""
        for i, exercise in enumerate(workout['exercises'], 1):
            workout_text += f"\n{i}. {exercise}"

        workout_text += "\n\n💡 <b>Совет:</b> Начинай с разминки 5-10 минут!"

        keyboard = [
            [InlineKeyboardButton("✅ Выполнил тренировку", callback_data='workout_done')],
            [InlineKeyboardButton("🔄 Новая тренировка", callback_data='quick_workout')],
            [InlineKeyboardButton("🥗 План питания", callback_data='nutrition_plan')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(workout_text, reply_markup=reply_markup, parse_mode='HTML')

        # Обновляем лида
        db.update_lead_stage(user_id, 'engaged')

    async def send_nutrition(self, query):
        """Отправляет AI-план питания"""
        user_id = query.from_user.id
        user_data = db.get_user(user_id)

        nutrition = ai_engine.generate_nutrition_plan({
            'goals': user_data[5] if user_data else 'weight_loss'
        })

        nutrition_text = f"""
🥗 <b>ТВОЙ AI-ПЛАН ПИТАНИЯ</b>

🔥 <b>Калории:</b> {nutrition['calories']}

<b>План на день:</b>
• 🍳 <b>Завтрак:</b> {nutrition['meals']['breakfast']}
• 🍲 <b>Обед:</b> {nutrition['meals']['lunch']}
• 🍽️ <b>Ужин:</b> {nutrition['meals']['dinner']}
• 🍎 <b>Перекусы:</b> {nutrition['meals']['snacks']}

💡 <b>Совет:</b> Пей 2-3 литра воды в день!
        """

        keyboard = [
            [InlineKeyboardButton("💪 Тренировка", callback_data='quick_workout')],
            [InlineKeyboardButton("🛒 Список покупок", callback_data='shopping_list')],
            [InlineKeyboardButton("💬 Задать вопрос", callback_data='ai_chat')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(nutrition_text, reply_markup=reply_markup, parse_mode='HTML')

    async def start_ai_chat(self, query):
        """Запускает AI-чат"""
        chat_text = """
💬 <b>AI-ЧАТ АКТИВИРОВАН</b>

Задай мне любой вопрос о:
• 💪 Тренировках и упражнениях
• 🥗 Питании и диетах
• 🏃 Беге и кардио
• 🧘 Йоге и растяжке
• 🎯 Поставке целей
• 🔥 Мотивации

Я профессиональный AI-тренер и помогу с любым вопросом!

<b>Пиши свой вопрос:</b>
        """

        await query.edit_message_text(chat_text, parse_mode='HTML')

    async def handle_ai_chat(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обрабатывает AI-чат"""
        user_id = update.effective_user.id
        user_message = update.message.text

        # Показываем что думаем
        thinking_msg = await update.message.reply_text("🤔 Думаю над ответом...")

        # Получаем историю диалога
        user_data = db.get_user(user_id)
        history = []
        if user_data and user_data[14]:  # conversation_history
            history = json.loads(user_data[14])

        # Генерируем AI-ответ
        ai_response = await ai_engine.generate_ai_response(user_message, history)

        # Сохраняем в историю
        db.update_conversation(user_id, user_message, ai_response)

        # Удаляем "думаю" и отправляем ответ
        await thinking_msg.delete()
        await update.message.reply_text(ai_response, parse_mode='HTML')

        # Авто-продажа если уместно
        await self.check_auto_sale(update, user_id, user_message)

    async def check_auto_sale(self, update, user_id, user_message):
        """Проверяет возможность авто-продажи"""
        user_data = db.get_user(user_id)
        if not user_data:
            return

        workout_count = user_data[11] or 0
        subscription_type = user_data[8]

        # Триггеры для продаж
        sale_triggers = [
            ('хочу результат', 'Вижу твою мотивацию! Для максимальных результатов рекомендую Premium с персональным коучингом!'),
            ('не получается', 'Понимаю! С Premium доступом я буду корректировать твою программу ежедневно!'),
            ('плато', 'Это нормально! С моим AI-анализом мы преодолеем плато быстрее!'),
            ('скучно', 'Добавлю разнообразия! В Premium версии +200 упражнений и челленджей!')
        ]

        user_msg_lower = user_message.lower()
        for trigger, response in sale_triggers:
            if trigger in user_msg_lower and subscription_type == 'trial' and workout_count >= 2:
                keyboard = [
                    [InlineKeyboardButton("💎 Узнать о Premium", callback_data='premium_offer')],
                    [InlineKeyboardButton("💪 Продолжить тренировки", callback_data='quick_workout')]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)

                await update.message.reply_text(response, reply_markup=reply_markup)
                break

    async def show_alice_connection(self, query):
        """Показывает подключение к Яндекс Алисе"""
        alice_text = """
🎧 <b>ПОДКЛЮЧИ ЯНДЕКС АЛИСУ!</b>

Теперь я доступен в твоей Яндекс Станции! 🏠

<b>Что умею через Алису:</b>
• 🎯 Голосовые тренировки
• 🥗 Советы по питанию
• 📊 Прогресс голосом
• 💪 Мотивация в реальном времени

<b>Как подключить:</b>
1. Скажи: <i>"Алиса, запусти навык Фитнес Тренер"</i>
2. Или найди в каталоге: <i>"AI Fitness Coach"</i>

<b>Буду твоим голосовым тренером дома! 🏋️</b>
        """

        keyboard = [
            [InlineKeyboardButton("💪 Получить тренировку", callback_data='quick_workout')],
            [InlineKeyboardButton("🏠 В главное меню", callback_data='main_menu')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(alice_text, reply_markup=reply_markup, parse_mode='HTML')

    async def show_premium_offer(self, query):
        """Показывает оффер Premium"""
        premium_text = """
💎 <b>PREMIUM ДОСТУП</b>

<b>Что получишь:</b>
• 🏋️ <b>Ежедневные AI-тренировки</b> - уникальные каждый день
• 🥗 <b>Персональное питание</b> - с учетом твоих предпочтений
• 📊 <b>AI-анализ прогресса</b> - фото, замеры, метрики
• 💬 <b>Приоритетная поддержка</b> - ответы за 5 минут
• 🎯 <b>Корректировка программ</b> - на основе твоих результатов
• 🔔 <b>Умные напоминания</b> - в лучшее для тебя время

<b>Всего 290/мес</b> - меньше 10р в день!

🚀 <b>Гарантия результата или верну деньги!</b>
        """

        keyboard = [
            [InlineKeyboardButton("💳 Оформить Premium", callback_data='buy_premium')],
            [InlineKeyboardButton("💪 Продолжить trial", callback_data='quick_workout')],
            [InlineKeyboardButton("💬 Консультация", callback_data='ai_chat')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(premium_text, reply_markup=reply_markup, parse_mode='HTML')

    async def send_reminders(self, context: ContextTypes.DEFAULT_TYPE):
        """Отправляет умные напоминания"""
        try:
            # Здесь будет логика отправки напоминаний
            # Пока просто логируем
            logger.info("🔔 Проверка напоминаний...")
        except Exception as e:
            logger.error(f"Ошибка в напоминаниях: {e}")

    async def quick_workout(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Быстрая тренировка по команде"""
        keyboard = [[InlineKeyboardButton("💪 Получить тренировку", callback_data='quick_workout')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("Нажми для персональной AI-тренировки!", reply_markup=reply_markup)

    async def quick_nutrition(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Быстрый план питания по команде"""
        keyboard = [[InlineKeyboardButton("🥗 Получить питание", callback_data='nutrition_plan')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("Нажми для AI-плана питания!", reply_markup=reply_markup)

    async def show_progress(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показывает прогресс"""
        user_id = update.effective_user.id
        user_data = db.get_user(user_id)

        if user_data:
            progress_text = f"""
📊 <b>ТВОЙ ПРОГРЕСС</b>

💪 <b>Тренировок выполнено:</b> {user_data[11] or 0}
🎯 <b>Цель:</b> {user_data[5] or 'Не указана'}
⚡ <b>Уровень:</b> {user_data[6] or 'Начинающий'}

🚀 <b>Совет:</b> Продолжай в том же духе!
            """
        else:
            progress_text = "Сначала запусти /start для регистрации"

        await update.message.reply_text(progress_text, parse_mode='HTML')

    def run(self):
        """Запускает бота"""
        logger.info("🚀 PRO Fitness Bot запускается...")
        self.application.run_polling()

class SalesAutomation:
    """Автоматизация продаж"""

    def __init__(self):
        self.auto_messages = {
            'day1': "Как твои первые впечатления? Нужна помощь с тренировкой? 💪",
            'day3': "Вижу ты активен! Хочешь получить расширенную программу? 🚀",
            'day7': "Trial заканчивается! Успей оформить Premium со скидкой 20%! 💎"
        }

    async def send_auto_message(self, bot, user_id, message_type):
        """Отправляет авто-сообщение"""
        try:
            message = self.auto_messages.get(message_type)
            if message:
                await bot.send_message(user_id, message)
        except Exception as e:
            logger.warning(f"Не удалось отправить авто-сообщение: {e}")

def main():
    try:
        bot = FitFriends_bot(config.BOT_TOKEN)
        bot.run()
    except Exception as e:
        logger.error(f"❌ Ошибка запуска: {e}")
        print(f"КРИТИЧЕСКАЯ ОШИБКА: {e}")
        print("Проверьте токен бота в файле .env")

if __name__ == '__main__':
    main()