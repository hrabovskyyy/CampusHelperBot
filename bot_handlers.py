from telebot import types
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from attendance import start_attendance_check, handle_attendance_response, save_attendance_to_csv, send_attendance_to_admin
from user_management import is_user_in_whitelist, is_user_admin, approve_user, add_user_to_whitelist, get_all_admins
from invites import add_invite_button_for_admin, get_available_folders, get_invites_by_folder
from utils import broadcast_message
from config import INVITE_COLUMNS, BACK_BUTTON_TEXT
attendance_data = {}
user_data = {}
is_adding_id = {}

def register_handlers(bot):
    @bot.message_handler(commands=['start_attendance'])
    def handle_start_attendance(message):
        if is_user_admin(message.from_user.id):
            global attendance_data
            attendance_data = start_attendance_check(bot)
            bot.send_message(message.from_user.id, "Відправлено запит на присутність всім користувачам!")
        else:
            bot.send_message(message.from_user.id, "Тільки адміністратор може використовувати цю команду!")

    @bot.message_handler(commands=['yes', 'no'])
    def handle_yes_no(message):
        response = handle_attendance_response(message, attendance_data)
        bot.send_message(message.from_user.id, response)
        if message.text == '/no':
            bot.send_message(message.from_user.id, "Будь ласка, вкажіть причину вашої відсутності, використовуючи команду /report.")

    @bot.message_handler(commands=['send_attendance'])
    def handle_send_attendance(message):
        if is_user_admin(message.from_user.id):
            save_attendance_to_csv(attendance_data)
            for admin_id in get_all_admins():
                send_attendance_to_admin(bot, admin_id)
            bot.send_message(message.from_user.id, "Відмітки збережено і відправлено всім адміністраторам.")
        else:
            bot.send_message(message.from_user.id, "Тільки адміністратор може використовувати цю команду!")

    @bot.message_handler(commands=['report'])
    def handle_report(message):
        user_id = str(message.from_user.id)
        if is_user_in_whitelist(user_id):
            if user_id in attendance_data and attendance_data[user_id]['attendance'] == "Відсутній":
                bot.send_message(user_id, "Будь ласка, вкажіть причину вашої відсутності!")
                bot.register_next_step_handler(message, save_report)
            else:
                bot.send_message(user_id, "Ви не відмічені як відсутній сьогодні. Спочатку відмітьте свою відсутність командою /no.")
        else:
            bot.send_message(user_id, "У вас немає доступу до цієї команди!")

    @bot.message_handler(commands=['invites'])
    def handle_invites(message):
        show_folder_selection(message.chat.id)

    def show_folder_selection(chat_id):
        folders = get_available_folders()

        if not folders:
            bot.send_message(chat_id, "На жаль, доступних папок з інвайтами не знайдено.")
            return

        keyboard = InlineKeyboardMarkup()
        for folder in folders:
            keyboard.add(InlineKeyboardButton(folder, callback_data=f"folder:{folder}"))

        bot.send_message(chat_id,
                         "Оберіть папку для перегляду інвайтів:",
                         reply_markup=keyboard)

    @bot.callback_query_handler(func=lambda call: call.data.startswith("folder:"))
    def folder_invites_handler(call):
        folder = call.data.split(":")[1]
        invite_keyboard = create_invite_keyboard_by_folder(folder)

        if invite_keyboard:
            invite_keyboard.add(InlineKeyboardButton(BACK_BUTTON_TEXT, callback_data="back_to_folders"))
            bot.edit_message_text(f"Інвайти в папці '{folder}':",
                                  call.message.chat.id,
                                  call.message.message_id,
                                  reply_markup=invite_keyboard)
        else:
            bot.answer_callback_query(call.id, f"У папці '{folder}' не знайдено інвайтів.")
            show_folder_selection(call.message.chat.id)

    @bot.callback_query_handler(func=lambda call: call.data == "back_to_folders")
    def handle_back_to_folders(call):
        show_folder_selection(call.message.chat.id)

    def create_invite_keyboard_by_folder(folder):
        keyboard = InlineKeyboardMarkup()
        invites = get_invites_by_folder(folder)
        for invite in invites:
            keyboard.add(InlineKeyboardButton(invite['text'], callback_data=f"invite:{invite['url']}"))
        return keyboard

    @bot.callback_query_handler(func=lambda call: call.data.startswith("invite:"))
    def handle_invite_selection(call):
        url = call.data.split(":")[1]
        bot.send_message(call.id, f"Ви обрали інвайт з URL: {url}")
    @bot.callback_query_handler(func=lambda call: call.data.startswith("folder:"))
    def folder_invites_handler(call):
        folder = call.data.split(":")[1]
        invite_keyboard = create_invite_keyboard_by_folder(folder)

        if invite_keyboard:
            invite_keyboard.add(InlineKeyboardButton(BACK_BUTTON_TEXT, callback_data="back_to_folders"))
            bot.edit_message_text(f"Інвайти в папці '{folder}':",
                                  call.message.chat.id,
                                  call.message.message_id,
                                  reply_markup=invite_keyboard)
        else:
            bot.answer_callback_query(call.id, f"У папці '{folder}' не знайдено інвайтів.")
            show_folder_selection(call.message.chat.id)

    @bot.callback_query_handler(func=lambda call: call.data == "back_to_folders")
    def handle_back_to_folders(call):
        show_folder_selection(call.message.chat.id)


    @bot.callback_query_handler(func=lambda call: call.data.startswith("invite:"))
    def handle_invite_selection(call):
        url = call.data.split(":")[1]
        bot.answer_callback_query(call.id, f"Ви обрали інвайт з URL: {url}")
    @bot.message_handler(content_types=['text'])
    def get_text_messages(message):
        user_id = message.from_user.id

        if not is_user_in_whitelist(user_id):
            keyboard = types.InlineKeyboardMarkup()
            approve_button = types.InlineKeyboardButton(text="Схвалити",
                                                        callback_data=f"approve_{user_id}_{message.from_user.username}")
            keyboard.add(approve_button)
            for admin_id in get_all_admins():
                bot.send_message(admin_id, f"Користувач {message.from_user.username} (ID: {user_id}) запитує доступ.",
                                 reply_markup=keyboard)
            bot.send_message(user_id, "У вас немає доступу! Очікуйте схвалення від адміністратора.")
            return

        if message.text == "/start":
            bot.send_message(user_id,
                             "Привіт! Я – бот ІК-44, створений спеціально для студентів, щоб полегшити ваше навчання та організацію групових справ!")
            bot.send_message(user_id, "Для перегляду всіх команд веедіть /help")
        elif message.text == "/help":
            bot.send_message(user_id,
                             "Доступні команди:\n/yes - підтвердити присутність\n/no - відмітити відсутність\n/report - повідомити про причину відсутності")
        elif message.text == '/reg_new_id' and is_user_admin(user_id):
            bot.send_message(user_id, "Введіть ID або /cancel для скасування:")
            is_adding_id[user_id] = True
            bot.register_next_step_handler(message, add_user_to_whitelist)
        elif message.text == "/cancel" and user_id in is_adding_id and is_adding_id[user_id]:
            bot.send_message(user_id, "Операція додавання ID скасована!")
            is_adding_id[user_id] = False
        elif message.text.startswith("/broadcast") and is_user_admin(user_id):
            broadcast_text = message.text[len("/broadcast "):].strip()
            if broadcast_text:
                bot.send_message(user_id, "Починаю розсилку...")
                broadcast_message(bot, message, broadcast_text)
            else:
                bot.send_message(user_id, "Текст для розсилки не вказаний.")
        elif message.text == "/add_invite" and is_user_admin(user_id):
            bot.send_message(user_id, "Введіть текст кнопки або /cancel для скасування:")
            bot.register_next_step_handler(message, text_handler)
        else:
            bot.send_message(user_id, "Я вас не розумію! Напишіть /help для отримання списку команд.")



    @bot.callback_query_handler(func=lambda call: call.data.startswith("approve"))
    def callback_inline(call):
        if is_user_admin(call.from_user.id):
            approve_user(bot, call)
        else:
            bot.answer_callback_query(call.id, "У вас немає прав для схвалення користувачів.")

    def save_report(message):
        user_id = str(message.from_user.id)
        report = message.text

        if user_id in attendance_data:
            attendance_data[user_id]['report'] = report
            bot.send_message(user_id, "Ваш звіт збережено! Дякуємо за інформацію!")
            for admin_id in get_all_admins():
                bot.send_message(admin_id,
                                 f"Новий звіт від користувача {user_id} {message.from_user.username}:\nДата: {attendance_data[user_id]['date']}\nПричина: {report}")
        else:
            bot.send_message(user_id, "Не вдалося зберегти звіт. Спробуйте пізніше.")

    def text_handler(message):
        if message.text == "/cancel":
            bot.send_message(message.from_user.id, "Операція додавання кнопки скасована.")
            return
        INVITE_COLUMNS['text'] = message.text
        bot.send_message(message.from_user.id, "Тепер введіть URL для кнопки або /cancel для скасування:")
        bot.register_next_step_handler(message, url_handler)

    def url_handler(message):
        if message.text == "/cancel":
            bot.send_message(message.from_user.id, "Операція додавання кнопки скасована.")
            return
        INVITE_COLUMNS['url'] = message.text
        bot.send_message(message.from_user.id, "Вкажіть назву папки (або залиште порожнім для 'default'):")
        bot.register_next_step_handler(message, folder_handler)

    def folder_handler(message):
        folder = message.text.strip() if message.text.strip() else 'default'
        add_invite_button_for_admin(bot, message, INVITE_COLUMNS['text'], INVITE_COLUMNS['url'], folder)
        bot.send_message(message.from_user.id, f"Кнопка з запрошенням успішно додана в папку '{folder}'!")