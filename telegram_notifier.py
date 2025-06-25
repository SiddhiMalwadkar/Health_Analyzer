import requests

# ✅ Your Bot Token and Chat ID
BOT_TOKEN = 'your bot token'
CHAT_ID = 'your chatid'  # Siddhi's Telegram chat ID

def send_telegram_message(message):
    """
    Sends a message to your Telegram using your bot.
    """
    url = f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage'
    payload = {
        'chat_id': CHAT_ID,
        'text': message
    }

    try:
        response = requests.post(url, data=payload)
        if response.status_code == 200:
            print("✅ Telegram message sent successfully.")
        else:
            print(f"❌ Failed to send message. Response: {response.text}")
    except Exception as e:
        print(f"⚠️ Error sending message: {e}")
