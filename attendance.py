import csv
from datetime import datetime
from config import WHITE_LIST_FILE, ATTENDANCE_FILE, COLUMNS

def start_attendance_check(bot):
    current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    attendance_data = {}
    try:
        with open(WHITE_LIST_FILE, newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                try:
                    bot.send_message(row['id'], "Чи будете ви на парах? Відповідайте /yes або /no.")
                    attendance_data[row['id']] = {
                        "username": row['username'],
                        "name": row['name'],
                        "date": current_date,
                        "attendance": "Не відповів",
                        "report": ""
                    }
                except Exception as e:
                    print(f"Не вдалося відправити повідомлення користувачу з ID {row['id']}: {e}")
    except FileNotFoundError:
        print("Список білого списку порожній або відсутній.")
    return attendance_data

def handle_attendance_response(message, attendance_data):
    user_id = str(message.from_user.id)
    if user_id in attendance_data:
        attendance_data[user_id]['attendance'] = "Присутній" if message.text == '/yes' else "Відсутній"
        return "Дякую :)"
    else:
        return "Запит на відмітку не було відправлено або ви не в білому списку."

def save_attendance_to_csv(attendance_data):
    with open(ATTENDANCE_FILE, "a", newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=COLUMNS)
        if file.tell() == 0:
            writer.writeheader()
        for user_id, data in attendance_data.items():
            writer.writerow({
                "id": user_id,
                "username": data["username"],
                "name": data["name"],
                "date": data["date"],
                "attendance": data["attendance"],
                "report": data["report"]
            })

def send_attendance_to_admin(bot, admin_id):
    import os
    if os.path.exists(ATTENDANCE_FILE):
        with open(ATTENDANCE_FILE, 'rb') as file:
            bot.send_document(admin_id, file)
    else:
        bot.send_message(admin_id, "Файл з відмітками не знайдено!")