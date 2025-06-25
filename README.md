# 🩺 Health Analyzer
A personal health monitoring desktop application that allows users to upload PDF health reports, extract key health parameters, track trends, set reminders, and receive notifications via Telegram — all with a clean, intuitive UI.

🌟 Features

✅ **Secure Login System**  
- Admin and multiple user accounts  
- Credentials managed via CSV

✅ **Health Report Upload & Analysis**  
- Upload PDF reports  
- Automatically extract values (e.g., Hemoglobin, Glucose, Bilirubin)  
- Store and manage report history

✅ **Trend Visualization**  
- Generate graphs for Hemoglobin, Glucose, and Bilirubin  
- Track health changes over time

✅ **Monthly & Parameter-Specific Summaries**  
- Monthly breakdown of reports  
- View trends of individual parameters

✅ **Smart Reminder System**  
- Schedule test reminders or health tasks  
- Telegram bot integration for daily and pre-reminder notifications

✅ **Admin Privileges**  
- View reports and trends for any user  
- Compare two reports side by side  
- Manage report history and summaries

## 🛠️ Tech Stack
- **Frontend/UI**: Python `Tkinter`
- **Backend**: Python, `json`, `csv`, `datetime`, `re`
- **PDF Parsing**: `pdfplumber`
- **Graphing**: `matplotlib`
- **Reminder Notifications**: Telegram Bot API
- **Calendar Input**: `tkcalendar`

## 📂 Project Structure

📁 HealthAnalyzer/
main.py # Login system

dashboard_user.py # User dashboard functionality

dashboard_admin.py # Admin dashboard functionality

telegram_notifier.py # Telegram bot message sender

users.csv # User credentials

 report_history.json # Uploaded reports and extracted data
 
 keywords.txt # Keywords to extract from PDFs
 
README.md # Project documentation


**🔐 Default User Credentials**
| Role   | Username   | Password         |
|--------|------------|------------------|
| Admin  | Admin      | Siddhi03         |
| User   | Girish     | Girish12345      |  

**Installation**

1. Clone the repository:-
git clone https://github.com/your-username/health-analyzer.git
   
cd health-analyzer
   
Install dependencies:-

pip install pdfplumber tkcalendar matplotlib

Run the application:-

python main.py

**🛎️ Telegram Reminder Setup**
Create a Telegram Bot using @BotFather

Save the bot token in telegram_notifier.py

Add your chat ID to receive reminders

Use Task Scheduler (Windows) or cron (Linux/macOS) to run the daily reminder script



