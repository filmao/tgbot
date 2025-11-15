import telebot
import re
import time
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import os

TOKEN = os.getenv("BOT_TOKEN")  # токен из Render
CHANNEL_ID = -1003458990833
ADMIN_ID = 8339987136

bot = telebot.TeleBot(TOKEN, threaded=True)

user_state = {}
last_message_time = {}

banned_words = [
    "подписывайся", "подпишись", "вступай", "реклама",
    "рекламу", "перейди", "переходи", "купи", "продам",
    "скидка", "промо", "акция"
]

def is_advert(text):
    text_lower = text.lower()
    for word in banned_words:
        if word in text_lower:
            return True
    if re.search(r"(http://|https://|t\.me/|tg://|www\.)", text_lower):
        return True
    if re.search(r"@\w+", text_lower):
        return True
    if re.search(r"\.\w{2,4}", text_lower):
        return True
    return False


@bot.message_handler(commands=['start'])
def start(message):
    kb = InlineKeyboardMarkup()
    kb.add(
        InlineKeyboardButton("✍️ Написать сообщение", callback_data="write"),
        InlineKeyboardButton("📘 Правила", callback_data="rules")
    )
    bot.send_message(
        message.chat.id,
        "👋 Привет! Это *Подслушано*.\n\n"
        "Здесь ты можешь анонимно отправить сообщение на канал.",
        parse_mode="Markdown",
        reply_markup=kb
    )


@bot.callback_query_handler(func=lambda call: True)
def callback(call):

    if call.data == "write":
        user_state[call.from_user.id] = "writing"
        bot.send_message(call.message.chat.id, "✍️ Напиши своё сообщение:")

    elif call.data == "rules":
        bot.send_message(
            call.message.chat.id,
            "📘 *Правила:*\n1. Правил нет 😘",
            parse_mode="Markdown"
        )


@bot.message_handler(func=lambda msg: True, content_types=['text'])
def handle_text(message):

    user_id = message.from_user.id
    text = message.text.strip()

    if user_state.get(user_id) == "writing":

        now = time.time()
        last_time = last_message_time.get(user_id, 0)

        if now - last_time < 10:
            bot.reply_to(message, "⏳ Подожди чуть-чуть перед следующим сообщением.")
            return

        last_message_time[user_id] = now

        if is_advert(text):
            bot.reply_to(message, "❌ Реклама, ссылки и переходы запрещены.")
            return

        bot.send_message(
            CHANNEL_ID,
            f"<blockquote>{text}</blockquote>",
            parse_mode="HTML"
        )

        admin_kb = InlineKeyboardMarkup()
        admin_kb.add(
            InlineKeyboardButton("👤 Открыть профиль", url=f"tg://user?id={user_id}")
        )

        bot.send_message(
            ADMIN_ID,
            f"👤 *Новый аноним:*\n"
            f"ID: `{user_id}`\n\n"
            f"Текст:\n{text}",
            parse_mode="Markdown",
            reply_markup=admin_kb
        )

        bot.reply_to(
            message,
            f"Готово! Анонимно отправлено 🙌\n\n"
            f"🆔 *Твой ID:* `{user_id}`",
            parse_mode="Markdown"
        )

        user_state[user_id] = None


bot.polling(none_stop=True, interval=0, timeout=20)
