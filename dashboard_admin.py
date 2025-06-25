import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from tkcalendar import DateEntry
import pdfplumber
import os
import json
import csv
import re
from datetime import datetime
from telegram_notifier import send_telegram_message

REPORT_HISTORY_FILE = "report_history.json"
USERS_FILE = "users.csv"

# 🎨 Visual Constants
PRIMARY_COLOR = "#32de84"
LIGHT_BG = "#f1fdf6"
TEXT_COLOR = "#222"

# ✅ Extract date from report text
def extract_date_from_text(text):
    date_patterns = [
        r"\b\d{2}[-/]\d{2}[-/]\d{4}\b",
        r"\b\d{4}[-/]\d{2}[-/]\d{2}\b",
    ]
    for pattern in date_patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(0)
    return "Unknown"

class PDFAnalyzer:
    def __init__(self):
        self.keywords = self.load_keywords()
        self.report_history = self.load_report_history()
        self.users = self._load_users_from_csv()

    def _load_users_from_csv(self):
        users_list = []
        try:
            if os.path.exists(USERS_FILE):
                with open(USERS_FILE, "r", newline='') as file:
                    reader = csv.DictReader(file)
                    for row in reader:
                        if "username" in row:
                            users_list.append(row["username"])
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load users: {str(e)}")
        return users_list

    def load_keywords(self):
        if not os.path.exists("keywords.txt"):
            with open("keywords.txt", "w") as f:
                f.write("Hemoglobin\nPlatelet count\nGlucose\n")
            return ["Hemoglobin", "Platelet count", "Glucose"]
        with open("keywords.txt", "r") as f:
            return [line.strip() for line in f if line.strip()]

    def load_report_history(self):
        if os.path.exists(REPORT_HISTORY_FILE):
            with open(REPORT_HISTORY_FILE, "r") as f:
                try:
                    content = f.read()
                    return json.loads(content) if content else []
                except Exception:
                    return []
        return []

    def save_report_history(self):
        with open(REPORT_HISTORY_FILE, "w") as f:
            json.dump(self.report_history, f, indent=4)

    def extract_values(self, pdf_path, assigned_to_user):
        try:
            with pdfplumber.open(pdf_path) as pdf:
                text = ' '.join(page.extract_text() or "" for page in pdf.pages)
            if not text:
                messagebox.showwarning("PDF Content", "No readable text found.")
                return {}

            report_date = extract_date_from_text(text)
            results = {}
            normalized_text = re.sub(r'\s+', ' ', text).lower()
            for keyword in self.keywords:
                pattern = rf"{re.escape(keyword.lower())}\s*.*?(\d+(?:[.,]\d+)*)"
                match = re.search(pattern, normalized_text)
                if match:
                    try:
                        value = float(match.group(1).replace(',', '.'))
                        results[keyword] = value
                    except ValueError:
                        continue

            report_entry = {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "filename": os.path.basename(pdf_path),
                "assigned_to": assigned_to_user,
                "report_date": report_date,
                "results": results
            }
            self.report_history.append(report_entry)
            self.save_report_history()
            return results
        except Exception as e:
            messagebox.showerror("Error", f"Error processing PDF: {str(e)}")
            return {}

def show_dashboard(username):
    analyzer = PDFAnalyzer()

    def browse_file():
        selected_user = user_dropdown_var.get().strip()
        if not selected_user:
            messagebox.showwarning("User Selection", "Please select a user.")
            return
        file_path = filedialog.askopenfilename(title="Select Health Report", filetypes=[("PDF Files", "*.pdf")])
        if file_path:
            results = analyzer.extract_values(file_path, selected_user)
            display_results(results)
            update_history()
            compare_button.config(state=tk.DISABLED)

    def display_results(data):
        results_text.delete(1.0, tk.END)
        if not data:
            results_text.insert(tk.END, "No values found.")
        else:
            results_text.insert(tk.END, "Extracted Health Parameters:\n\n")
            for param, value in data.items():
                results_text.insert(tk.END, f"\u2022 {param}: {value}\n")

    def update_history():
        history_tree.delete(*history_tree.get_children())
        for i, report in enumerate(analyzer.report_history):
            history_tree.insert("", tk.END, iid=str(i), values=(
                report["timestamp"],
                report["filename"],
                report.get("assigned_to", "N/A"),
                len(report["results"])
            ))

    def compare_reports():
        selected_items = history_tree.selection()
        if len(selected_items) != 2:
            messagebox.showwarning("Comparison", "Select exactly two reports.")
            return
        idx1, idx2 = int(selected_items[0]), int(selected_items[1])
        r1, r2 = analyzer.report_history[idx1], analyzer.report_history[idx2]
        r1, r2 = sorted([r1, r2], key=lambda r: r["timestamp"])

        label1 = f"{r1['filename']} ({r1.get('report_date', 'N/A')})"
        label2 = f"{r2['filename']} ({r2.get('report_date', 'N/A')})"

        output = ["--- Report Comparison ---\n"]
        output.append(f"{'Parameter':<25} {label1:<30} {label2:<30}")
        output.append("-" * 90)

        all_params = sorted(set(r1["results"].keys()).union(r2["results"].keys()))
        for param in all_params:
            v1, v2 = r1["results"].get(param, "N/A"), r2["results"].get(param, "N/A")
            def fmt(v): return f"{v:.2f}" if isinstance(v, float) else str(v)
            symbol = "\u2796"
            if isinstance(v1, (int, float)) and isinstance(v2, (int, float)):
                if v2 > v1: symbol = "\u2B06"
                elif v2 < v1: symbol = "\u2B07"
            right = f"{fmt(v2)} {symbol}" if symbol != "\u2796" else fmt(v2)
            output.append(f"{param:<25} {fmt(v1):<30} {right:<30}")

        results_text.delete(1.0, tk.END)
        results_text.insert(tk.END, "\n".join(output))

    root = tk.Tk()
    root.title(f"Admin Dashboard - {username}")
    root.geometry("1000x700")
    root.configure(bg=LIGHT_BG)

    notebook = ttk.Notebook(root)
    notebook.pack(expand=True, fill="both")

    # Upload Tab
    analysis_frame = ttk.Frame(notebook)
    notebook.add(analysis_frame, text="Report Analysis")
    upload_frame = tk.Frame(analysis_frame, bg=LIGHT_BG, pady=10)
    upload_frame.pack(fill="x", padx=10, pady=10)

    tk.Label(upload_frame, text="Assign to User:", bg=LIGHT_BG, fg=TEXT_COLOR).pack(side=tk.LEFT, padx=5)
    user_dropdown_var = tk.StringVar(root)
    user_dropdown = ttk.Combobox(upload_frame, textvariable=user_dropdown_var,
                                 values=analyzer.users, state="readonly", width=20)
    if analyzer.users:
        user_dropdown_var.set(analyzer.users[0])
    user_dropdown.pack(side=tk.LEFT, padx=5)
    tk.Button(upload_frame, text="Browse PDF", command=browse_file,
              bg=PRIMARY_COLOR, fg="white", padx=10, pady=5).pack(side=tk.LEFT, padx=15)

    results_frame = tk.Frame(analysis_frame, bg=LIGHT_BG)
    results_frame.pack(expand=True, fill="both", padx=10, pady=10)
    results_text = tk.Text(results_frame, wrap=tk.WORD, font=("Consolas", 10))
    results_text.pack(expand=True, fill="both")
    scrollbar = ttk.Scrollbar(results_frame, command=results_text.yview)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    results_text.config(yscrollcommand=scrollbar.set)

    # History Tab
    history_frame = ttk.Frame(notebook)
    notebook.add(history_frame, text="Report History & Comparison")
    history_tree = ttk.Treeview(history_frame, columns=("Timestamp", "Filename", "Assigned To", "Parameters"),
                                show="headings", selectmode="extended")
    for col in ("Timestamp", "Filename", "Assigned To", "Parameters"):
        history_tree.heading(col, text=col)
    history_tree.pack(expand=True, fill="both", padx=10, pady=10)

    compare_button = tk.Button(history_frame, text="Compare Selected Reports",
                               command=compare_reports, state=tk.DISABLED,
                               bg=PRIMARY_COLOR, fg="white", width=25)
    compare_button.pack(pady=10)
    history_tree.bind("<<TreeviewSelect>>",
                      lambda event: compare_button.config(state=tk.NORMAL if len(history_tree.selection()) == 2 else tk.DISABLED))
    update_history()

    # Reminder Tab
    reminder_tab = ttk.Frame(notebook)
    notebook.add(reminder_tab, text="Reminders")
    reminder_tab.grid_columnconfigure(1, weight=1)

    tk.Label(reminder_tab, text="Title:").grid(row=0, column=0, padx=10, pady=10, sticky="e")
    title_entry = tk.Entry(reminder_tab, width=30)
    title_entry.grid(row=0, column=1, padx=10, pady=10)

    tk.Label(reminder_tab, text="Type:").grid(row=1, column=0, padx=10, pady=10, sticky="e")
    type_entry = ttk.Combobox(reminder_tab, values=["Test", "Appointment", "Medication"], width=28)
    type_entry.grid(row=1, column=1, padx=10, pady=10)

    tk.Label(reminder_tab, text="Date:").grid(row=2, column=0, padx=10, pady=10, sticky="e")
    date_entry = DateEntry(reminder_tab, date_pattern='yyyy-mm-dd')
    date_entry.grid(row=2, column=1, padx=10, pady=10)

    def save_reminder():
        reminder = {
            "title": title_entry.get().strip(),
            "type": type_entry.get().strip(),
            "date": date_entry.get_date().strftime("%Y-%m-%d")
        }
        try:
            if not os.path.exists("reminders.json"):
                with open("reminders.json", "w") as f:
                    json.dump([], f)
            with open("reminders.json", "r") as f:
                data = json.load(f)
            data.append(reminder)
            with open("reminders.json", "w") as f:
                json.dump(data, f, indent=4)
            messagebox.showinfo("Success", "Reminder saved successfully!")
            send_telegram_message(
                f"\u2705 Reminder added\n\n• {reminder['title']}\n• {reminder['type']}\n• Date: {reminder['date']}")
            load_reminders()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save reminder: {e}")

    save_button = tk.Button(reminder_tab, text="\ud83d\udcc0 Save Reminder", command=save_reminder, bg=PRIMARY_COLOR, fg="white")
    save_button.grid(row=3, column=1, padx=10, pady=10, sticky="e")

    reminder_list = ttk.Treeview(reminder_tab, columns=("Title", "Type", "Date"), show="headings")
    for col in ("Title", "Type", "Date"):
        reminder_list.heading(col, text=col)
    reminder_list.grid(row=4, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")

    def load_reminders():
        for row in reminder_list.get_children():
            reminder_list.delete(row)
        if os.path.exists("reminders.json"):
            with open("reminders.json", "r") as f:
                for r in json.load(f):
                    reminder_list.insert("", tk.END, values=(r["title"], r["type"], r["date"]))

    load_reminders()
    root.mainloop()
