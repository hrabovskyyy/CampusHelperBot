import telebot
from bot_handlers import register_handlers
from scheduler import start_scheduler
from config import BOT_TOKEN

def main():
    bot = telebot.TeleBot(BOT_TOKEN)
    register_handlers(bot)
    start_scheduler(bot)
    bot.polling(none_stop=True, interval=0)

if __name__ == "__main__":
    main()