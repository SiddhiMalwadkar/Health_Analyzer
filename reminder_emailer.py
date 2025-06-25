import json
import os
from datetime import datetime, timedelta
from telegram_notifier import send_telegram_message

REMINDER_FILE = "reminders.json"
LOG_FILE = "reminder_log.txt"

def log(message):
    with open(LOG_FILE, "a") as f:
        f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}\n")

def load_reminders():
    try:
        with open(REMINDER_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        log(f"❌ Failed to load reminders: {e}")
        return []

def check_and_notify():
    today = datetime.now().date()
    tomorrow = today + timedelta(days=1)
    reminders = load_reminders()

    if not reminders:
        log("ℹ️ No reminders found.")
        return

    sent_any = False
    for reminder in reminders:
        try:
            r_date = datetime.strptime(reminder["date"], "%Y-%m-%d").date()
            days_left = (r_date - today).days

            if days_left in [0, 1]:  # Today or Tomorrow
                emoji = "📅" if days_left == 0 else "⏰"
                timing = "Today" if days_left == 0 else "Tomorrow"
                message = (
                    f"{emoji} Reminder: Your {reminder['type'].lower()} is scheduled.\n\n"
                    f"• Title: {reminder['title']}\n"
                    f"• Date: {reminder['date']} ({timing})\n\n"
                    f"🩺 Stay healthy!"
                )
                send_telegram_message(message)
                log(f"✅ Reminder sent for '{reminder['title']}' scheduled {timing}.")
                sent_any = True
        except Exception as e:
            log(f"⚠️ Skipped invalid reminder: {reminder} | Error: {e}")

    if not sent_any:
        log("📭 No reminders to send today or tomorrow.")

if __name__ == "__main__":
    check_and_notify()
