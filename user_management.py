import csv
from config import WHITE_LIST_FILE, WHITE_LIST_COLUMNS

def is_user_in_whitelist(user_id):
    try:
        with open(WHITE_LIST_FILE, newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            return any(str(user_id) == row['id'] for row in reader)
    except FileNotFoundError:
        return False

def is_user_admin(user_id):
    try:
        with open(WHITE_LIST_FILE, newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                if str(user_id) == row['id']:
                    return row['is_admin'] == 'true'
    except FileNotFoundError:
        return False
    return False

def add_user_to_whitelist(user_data):
    with open(WHITE_LIST_FILE, "a", newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=WHITE_LIST_COLUMNS)
        if file.tell() == 0:
            writer.writeheader()
        writer.writerow(user_data)

def approve_user(bot, call):
    user_id, username = call.data.split("_")[1:]
    user_data = {
        "id": user_id,
        "username": username,
        "name": "N/A",
        "is_admin": "false"  # New users are not admins by default
    }
    add_user_to_whitelist(user_data)
    bot.send_message(user_id, "Вам надано доступ до боту! Приємного користування!")
    bot.send_message(call.message.chat.id, f"Користувач {username} (ID: {user_id}) доданий в список.")

def get_all_admins():
    admins = []
    try:
        with open(WHITE_LIST_FILE, newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                if row['is_admin'].lower() == 'true':
                    admins.append(row['id'])
    except FileNotFoundError:
        pass
    return admins