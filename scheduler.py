import schedule
import time
from datetime import datetime
import threading
from attendance import start_attendance_check


def auto_attendance_check(bot):
    current_time = datetime.now().time()
    if current_time.hour == 8 and current_time.minute == 0:
        start_attendance_check(bot)

def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(1)

def start_scheduler(bot):
    schedule.every().day.at("08:00").do(auto_attendance_check, bot)
    scheduler_thread = threading.Thread(target=run_scheduler, args=(bot,))
    scheduler_thread.start()