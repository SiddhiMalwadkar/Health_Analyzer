import tkinter as tk
from tkinter import messagebox, filedialog, ttk
from tkcalendar import DateEntry
import os
import json
import shutil
import re
import pdfplumber
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from telegram_notifier import send_telegram_message

KEY_PARAMS = ["Hemoglobin", "Glucose", "Bilirubin"]
REPORT_HISTORY_FILE = "report_history.json"

# Colors for enhanced UI
PRIMARY_COLOR = "#32de84"        # main green
ACCENT_COLOR = "#28c673"         # slightly darker
LIGHT_BG = "#e6f9f0"             # light background
FRAME_BG = "#c0f2dc"             # container/frame bg
TEXT_COLOR = "#1f5131"           # darker text


def extract_basic_values(pdf_path):
    results = {}
    try:
        with pdfplumber.open(pdf_path) as pdf:
            text = " ".join(page.extract_text() or "" for page in pdf.pages)

        normalized = re.sub(r"\s+", " ", text).lower()
        for param in KEY_PARAMS:
            pattern = rf"{param.lower()}.*?(\d+(?:[.,]\d+)?)"
            match = re.search(pattern, normalized)
            if match:
                try:
                    val = float(match.group(1).replace(',', '.'))
                    results[param] = val
                except ValueError:
                    continue
    except Exception as e:
        messagebox.showerror("Error", f"Failed to extract values: {e}")
    return results


def show_dashboard(username):
    root = tk.Tk()
    root.title(f"Health Analyzer - {username}")
    root.geometry("900x650")
    root.configure(bg=LIGHT_BG)

    header = tk.Label(root, text=f"Welcome, {username}!", font=("Segoe UI", 18, "bold"), fg=PRIMARY_COLOR, bg=LIGHT_BG)
    header.pack(pady=20)

    notebook = tk.Frame(root, bg=LIGHT_BG)
    notebook.pack(fill="both", expand=True)

    # --- Upload Report Frame ---
    upload_frame = tk.LabelFrame(notebook, text="Upload Report", font=("Segoe UI", 12, "bold"), bg=FRAME_BG,
                                  fg=TEXT_COLOR, padx=15, pady=15, bd=2, relief="groove")
    upload_frame.pack(fill="x", padx=20, pady=10)

    tk.Label(upload_frame, text="Select PDF Health Report:", font=("Segoe UI", 11), bg=FRAME_BG,
             fg=TEXT_COLOR).pack(pady=10)

    def upload_report():
        file_path = filedialog.askopenfilename(title="Select Health Report PDF", filetypes=[("PDF Files", "*.pdf")])
        if file_path:
            try:
                os.makedirs(f"user_reports/{username}", exist_ok=True)
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                new_filename = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                dest_path = f"user_reports/{username}/{new_filename}"
                shutil.copy(file_path, dest_path)

                extracted = extract_basic_values(file_path)
                report_entry = {
                    "timestamp": timestamp,
                    "filename": new_filename,
                    "assigned_to": username,
                    "results": extracted
                }

                if not os.path.exists(REPORT_HISTORY_FILE):
                    with open(REPORT_HISTORY_FILE, "w") as f:
                        json.dump([], f)

                with open(REPORT_HISTORY_FILE, "r") as f:
                    history = json.load(f)
                history.append(report_entry)
                with open(REPORT_HISTORY_FILE, "w") as f:
                    json.dump(history, f, indent=4)

                messagebox.showinfo("Success", "Report uploaded successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to upload: {e}")

    def show_trends():
        if not os.path.exists(REPORT_HISTORY_FILE):
            messagebox.showwarning("No Data", "No report data found.")
            return

        with open(REPORT_HISTORY_FILE, "r") as f:
            all_reports = json.load(f)

        user_reports = [r for r in all_reports if r.get("assigned_to") == username and "results" in r]
        if not user_reports:
            messagebox.showinfo("No Reports", "No reports found.")
            return

        user_reports.sort(key=lambda x: datetime.strptime(x["timestamp"], "%Y-%m-%d %H:%M:%S"))
        dates = [datetime.strptime(r["timestamp"], "%Y-%m-%d %H:%M:%S") for r in user_reports]

        fig, ax = plt.subplots(figsize=(8, 4))
        for param in KEY_PARAMS:
            values = [r["results"].get(param, None) for r in user_reports]
            ax.plot(dates, values, marker='o', label=param)

        ax.set_title("Health Parameter Trends", fontsize=12)
        ax.set_xlabel("Date")
        ax.set_ylabel("Values")
        ax.legend()
        ax.grid(True)

        top = tk.Toplevel(root)
        top.title("Trends Overview")
        canvas = FigureCanvasTkAgg(fig, master=top)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    tk.Button(upload_frame, text="Upload PDF", command=upload_report,
              bg=PRIMARY_COLOR, fg="white", font=("Segoe UI", 10, "bold"), relief="flat",
              activebackground=ACCENT_COLOR, padx=10, pady=5).pack(pady=5)

    tk.Button(upload_frame, text="View My Trends", command=show_trends,
              bg=PRIMARY_COLOR, fg="white", font=("Segoe UI", 10, "bold"), relief="flat",
              activebackground=ACCENT_COLOR, padx=10, pady=5).pack(pady=5)

    tk.Button(upload_frame, text="📆 Monthly Summary", command=lambda: show_monthly_summary(root, username),
              bg=PRIMARY_COLOR, fg="white", font=("Segoe UI", 10, "bold"),
              relief="flat", activebackground=ACCENT_COLOR, padx=10, pady=5).pack(pady=5)

    tk.Button(upload_frame, text="📈 Parameter Summary", command=lambda: show_parameter_summary(root, username),
              bg=PRIMARY_COLOR, fg="white", font=("Segoe UI", 10, "bold"),
              relief="flat", activebackground=ACCENT_COLOR, padx=10, pady=5).pack(pady=5)

    # --- Reminder Frame ---
    reminder_frame = tk.LabelFrame(notebook, text="Set Reminder", font=("Segoe UI", 12, "bold"), bg=FRAME_BG,
                                    fg=TEXT_COLOR, padx=15, pady=15, bd=2, relief="groove")
    reminder_frame.pack(fill="x", padx=20, pady=10)

    tk.Label(reminder_frame, text="Reminder Title:", bg=FRAME_BG, fg=TEXT_COLOR, font=("Segoe UI", 10)).grid(row=0, column=0, padx=10, pady=5, sticky="e")
    title_entry = tk.Entry(reminder_frame, width=30)
    title_entry.grid(row=0, column=1, padx=10, pady=5)

    tk.Label(reminder_frame, text="Type:", bg=FRAME_BG, fg=TEXT_COLOR, font=("Segoe UI", 10)).grid(row=1, column=0, padx=10, pady=5, sticky="e")
    type_entry = tk.Entry(reminder_frame, width=30)
    type_entry.grid(row=1, column=1, padx=10, pady=5)

    tk.Label(reminder_frame, text="Date:", bg=FRAME_BG, fg=TEXT_COLOR, font=("Segoe UI", 10)).grid(row=2, column=0, padx=10, pady=5, sticky="e")
    date_entry = DateEntry(reminder_frame, date_pattern="yyyy-mm-dd")
    date_entry.grid(row=2, column=1, padx=10, pady=5)

    def show_monthly_summary(root, username):
        try:
            if not os.path.exists(REPORT_HISTORY_FILE):
                messagebox.showwarning("No Data", "No report data found.")
                return

            with open(REPORT_HISTORY_FILE, "r") as f:
                all_reports = json.load(f)

            user_reports = [
                r for r in all_reports if r.get("assigned_to") == username and "results" in r
            ]

            if not user_reports:
                messagebox.showinfo("No Reports", "No reports found for summary.")
                return

            summary_data = {}
            for report in user_reports:
                month = datetime.strptime(report["timestamp"], "%Y-%m-%d %H:%M:%S").strftime("%Y-%m")
                if month not in summary_data:
                    summary_data[month] = {param: [] for param in KEY_PARAMS}
                for param in KEY_PARAMS:
                    val = report["results"].get(param)
                    if isinstance(val, (int, float)):
                        summary_data[month][param].append(val)

            output = ["📅 Monthly Summary:\n"]
            for month, params in sorted(summary_data.items()):
                output.append(f"Month: {month}")
                for param, values in params.items():
                    if values:
                        avg = sum(values) / len(values)
                        output.append(f"• {param}: Avg = {avg:.2f}, Min = {min(values)}, Max = {max(values)}")
                output.append("")

            messagebox.showinfo("Monthly Summary", "\n".join(output))

        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate summary: {e}")

    def show_parameter_summary(root, username):
        try:
            if not os.path.exists(REPORT_HISTORY_FILE):
                messagebox.showwarning("No Data", "No report data found.")
                return

            with open(REPORT_HISTORY_FILE, "r") as f:
                all_reports = json.load(f)

            user_reports = [
                r for r in all_reports if r.get("assigned_to") == username and "results" in r
            ]

            if not user_reports:
                messagebox.showinfo("No Reports", "No reports found.")
                return

            all_params = set()
            for r in user_reports:
                all_params.update(r["results"].keys())

            if not all_params:
                messagebox.showinfo("No Data", "No parameters available.")
                return

            param_window = tk.Toplevel(root)
            param_window.title("📈 Parameter Summary")
            param_window.configure(bg=LIGHT_BG)

            tk.Label(param_window, text="Choose a parameter:", font=("Segoe UI", 11), bg=LIGHT_BG, fg=TEXT_COLOR).pack(
                pady=10)

            param_var = tk.StringVar(param_window)
            param_box = ttk.Combobox(param_window, textvariable=param_var, values=sorted(all_params), state="readonly",
                                     width=30)
            param_box.pack(pady=5)
            param_box.set("Hemoglobin")

            def show_plot():
                param = param_var.get()
                dates, values = [], []

                for r in user_reports:
                    val = r["results"].get(param)
                    if isinstance(val, (int, float)):
                        dt = datetime.strptime(r["timestamp"], "%Y-%m-%d %H:%M:%S")
                        dates.append(dt)
                        values.append(val)

                if not values:
                    messagebox.showinfo("No Data", f"No values found for {param}")
                    return

                fig, ax = plt.subplots(figsize=(7, 4))
                ax.plot(dates, values, marker='o', label=param, color="#2e7d32")
                ax.set_title(f"{param} Trend - {username}")
                ax.set_xlabel("Date")
                ax.set_ylabel("Value")
                ax.grid(True)
                ax.legend()

                chart_win = tk.Toplevel(param_window)
                chart_win.title(f"{param} Summary")
                canvas = FigureCanvasTkAgg(fig, master=chart_win)
                canvas.draw()
                canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

            tk.Button(param_window, text="📊 Show Summary", command=show_plot,
                      bg=PRIMARY_COLOR, fg="white", font=("Segoe UI", 10, "bold"),
                      relief="flat", activebackground=ACCENT_COLOR,
                      padx=10, pady=5).pack(pady=15)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to show parameter summary: {e}")

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
                f"\u2705 Hi {username}, your {reminder['type']} reminder is scheduled.\n\nTitle: {reminder['title']}\nDate: {reminder['date']}"
            )
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save reminder: {e}")

    tk.Button(reminder_frame, text="Save Reminder", command=save_reminder,
              bg=PRIMARY_COLOR, fg="white", font=("Segoe UI", 10, "bold"), relief="flat",
              activebackground=ACCENT_COLOR, padx=10, pady=5).grid(row=3, column=1, pady=15, sticky="e")

    root.mainloop()

#  import tkinter as tk
# from tkinter import ttk, messagebox, filedialog
# from tkcalendar import DateEntry
# import os
# import json
# import shutil
# import re
# import pdfplumber
# from datetime import datetime
# import matplotlib.pyplot as plt
# from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
# from telegram_notifier import send_telegram_message
#
# KEY_PARAMS = ["Hemoglobin", "Glucose", "Bilirubin"]
# REPORT_HISTORY_FILE = "report_history.json"
#
# def extract_basic_values(pdf_path):
#     results = {}
#     try:
#         with pdfplumber.open(pdf_path) as pdf:
#             text = " ".join(page.extract_text() or "" for page in pdf.pages)
#
#         normalized = re.sub(r"\s+", " ", text).lower()
#         for param in KEY_PARAMS:
#             pattern = rf"{param.lower()}.*?(\d+(?:[.,]\d+)?)"
#             match = re.search(pattern, normalized)
#             if match:
#                 try:
#                     val = float(match.group(1).replace(',', '.'))
#                     results[param] = val
#                 except ValueError:
#                     continue
#     except Exception as e:
#         messagebox.showerror("Error", f"Failed to extract values: {e}")
#     return results
#
# def show_dashboard(username):
#     root = tk.Tk()
#     root.title(f"Patient Dashboard - {username}")
#     root.geometry("800x600")
#
#     notebook = ttk.Notebook(root)
#     notebook.pack(expand=True, fill="both")
#
#     # --- Health Summary Tab ---
#     summary_frame = ttk.Frame(notebook)
#     notebook.add(summary_frame, text="Health Summary")
#     tk.Label(summary_frame, text=f"Welcome, {username}!", font=("Arial", 14, "bold")).pack(pady=20)
#
#     # --- Upload Report Tab ---
#     upload_frame = ttk.Frame(notebook)
#     notebook.add(upload_frame, text="Upload Report")
#     tk.Label(upload_frame, text="Select PDF Health Report:", font=("Arial", 12)).pack(pady=10)
#
#     def upload_report():
#         file_path = filedialog.askopenfilename(
#             title="Select Health Report PDF",
#             filetypes=[("PDF Files", "*.pdf")]
#         )
#         if file_path:
#             try:
#                 os.makedirs(f"user_reports/{username}", exist_ok=True)
#                 timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
#                 new_filename = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
#                 dest_path = f"user_reports/{username}/{new_filename}"
#                 shutil.copy(file_path, dest_path)
#
#                 extracted = extract_basic_values(file_path)
#                 report_entry = {
#                     "timestamp": timestamp,
#                     "filename": new_filename,
#                     "assigned_to": username,
#                     "results": extracted
#                 }
#
#                 if not os.path.exists(REPORT_HISTORY_FILE):
#                     with open(REPORT_HISTORY_FILE, "w") as f:
#                         json.dump([], f)
#
#                 with open(REPORT_HISTORY_FILE, "r") as f:
#                     history = json.load(f)
#
#                 history.append(report_entry)
#
#                 with open(REPORT_HISTORY_FILE, "w") as f:
#                     json.dump(history, f, indent=4)
#
#                 messagebox.showinfo("Success", "Report uploaded and saved successfully!")
#             except Exception as e:
#                 messagebox.showerror("Error", f"Failed to upload: {e}")
#
#     def show_trends():
#         if not os.path.exists(REPORT_HISTORY_FILE):
#             messagebox.showwarning("No Data", "No report data found.")
#             return
#
#         with open(REPORT_HISTORY_FILE, "r") as f:
#             all_reports = json.load(f)
#
#         user_reports = [
#             r for r in all_reports if r.get("assigned_to") == username and "results" in r
#         ]
#         if not user_reports:
#             messagebox.showinfo("No Reports", "You have not uploaded any reports yet.")
#             return
#
#         user_reports.sort(key=lambda x: datetime.strptime(x["timestamp"], "%Y-%m-%d %H:%M:%S"))
#         dates = [datetime.strptime(r["timestamp"], "%Y-%m-%d %H:%M:%S") for r in user_reports]
#         hemoglobin = [r["results"].get("Hemoglobin", None) for r in user_reports]
#         glucose = [r["results"].get("Glucose", None) for r in user_reports]
#         bilirubin = [r["results"].get("Bilirubin", None) for r in user_reports]
#
#         fig, ax = plt.subplots(figsize=(7, 4))
#         ax.plot(dates, hemoglobin, marker='o', label="Hemoglobin")
#         ax.plot(dates, glucose, marker='s', label="Glucose")
#         ax.plot(dates, bilirubin, marker='^', label="Bilirubin")
#         ax.set_title(f"Health Trends - {username}")
#         ax.set_xlabel("Date")
#         ax.set_ylabel("Value")
#         ax.legend()
#         ax.grid(True)
#
#         top = tk.Toplevel(root)
#         top.title("Health Trends")
#         canvas = FigureCanvasTkAgg(fig, master=top)
#         canvas.draw()
#         canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
#
#     def show_monthly_summary():
#         try:
#             if not os.path.exists(REPORT_HISTORY_FILE):
#                 messagebox.showwarning("No Data", "No report data found.")
#                 return
#
#             with open(REPORT_HISTORY_FILE, "r") as f:
#                 all_reports = json.load(f)
#
#             user_reports = [
#                 r for r in all_reports if r.get("assigned_to") == username and "results" in r
#             ]
#
#             if not user_reports:
#                 messagebox.showinfo("No Reports", "No reports found for summary.")
#                 return
#
#             summary_data = {}
#             for report in user_reports:
#                 month = datetime.strptime(report["timestamp"], "%Y-%m-%d %H:%M:%S").strftime("%Y-%m")
#                 if month not in summary_data:
#                     summary_data[month] = {param: [] for param in KEY_PARAMS}
#                 for param in KEY_PARAMS:
#                     val = report["results"].get(param)
#                     if isinstance(val, (int, float)):
#                         summary_data[month][param].append(val)
#
#             output = ["📅 Monthly Summary:\n"]
#             for month, params in sorted(summary_data.items()):
#                 output.append(f"Month: {month}")
#                 for param, values in params.items():
#                     if values:
#                         avg = sum(values)/len(values)
#                         output.append(f"• {param}: Avg = {avg:.2f}, Min = {min(values)}, Max = {max(values)}")
#                 output.append("")
#
#             messagebox.showinfo("Monthly Summary", "\n".join(output))
#
#         except Exception as e:
#             messagebox.showerror("Error", f"Failed to generate summary: {e}")
#
#     def show_parameter_summary():
#         try:
#             if not os.path.exists(REPORT_HISTORY_FILE):
#                 messagebox.showwarning("No Data", "No report data found.")
#                 return
#
#             with open(REPORT_HISTORY_FILE, "r") as f:
#                 all_reports = json.load(f)
#
#             user_reports = [
#                 r for r in all_reports if r.get("assigned_to") == username and "results" in r
#             ]
#
#             if not user_reports:
#                 messagebox.showinfo("No Reports", "No reports found.")
#                 return
#
#             all_params = set()
#             for r in user_reports:
#                 all_params.update(r["results"].keys())
#
#             if not all_params:
#                 messagebox.showinfo("No Data", "No parameters available.")
#                 return
#
#             param_window = tk.Toplevel()
#             param_window.title("Select Parameter")
#             tk.Label(param_window, text="Choose a parameter:").pack(pady=10)
#
#             param_var = tk.StringVar(param_window)
#             param_box = ttk.Combobox(param_window, textvariable=param_var, values=sorted(all_params), state="readonly")
#             param_box.pack(pady=5)
#             param_box.set("Hemoglobin")
#
#             def show_plot():
#                 param = param_var.get()
#                 dates, values = [], []
#
#                 for r in user_reports:
#                     val = r["results"].get(param)
#                     if isinstance(val, (int, float)):
#                         dt = datetime.strptime(r["timestamp"], "%Y-%m-%d %H:%M:%S")
#                         dates.append(dt)
#                         values.append(val)
#
#                 if not values:
#                     messagebox.showinfo("No Data", f"No values found for {param}")
#                     return
#
#                 fig, ax = plt.subplots(figsize=(6, 4))
#                 ax.plot(dates, values, marker='o', label=param)
#                 ax.set_title(f"{param} Trend")
#                 ax.set_xlabel("Date")
#                 ax.set_ylabel("Value")
#                 ax.grid(True)
#                 ax.legend()
#
#                 chart_win = tk.Toplevel(param_window)
#                 chart_win.title(f"{param} Summary")
#                 canvas = FigureCanvasTkAgg(fig, master=chart_win)
#                 canvas.draw()
#                 canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
#
#             tk.Button(param_window, text="Show Summary", command=show_plot).pack(pady=10)
#
#         except Exception as e:
#             messagebox.showerror("Error", f"Failed to show parameter summary: {e}")
#
#     tk.Button(upload_frame, text="Upload PDF", command=upload_report, bg="#4CAF50", fg="white", width=15).pack(pady=10)
#     tk.Button(upload_frame, text="📊 View My Trends", command=show_trends, bg="#2196F3", fg="white", width=15).pack(pady=5)
#     tk.Button(upload_frame, text="📆 Monthly Summary", command=show_monthly_summary, bg="#795548", fg="white", width=20).pack(pady=5)
#     tk.Button(upload_frame, text="📈 Parameter Summary", command=show_parameter_summary, bg="#3F51B5", fg="white", width=20).pack(pady=5)
#
#     # --- Reminder Tab ---
#     reminder_frame = ttk.Frame(notebook)
#     notebook.add(reminder_frame, text="Schedule Reminder")
#
#     tk.Label(reminder_frame, text="Reminder Title:").grid(row=0, column=0, padx=10, pady=10, sticky="e")
#     title_entry = tk.Entry(reminder_frame, width=30)
#     title_entry.grid(row=0, column=1, padx=10, pady=10)
#
#     tk.Label(reminder_frame, text="Type:").grid(row=1, column=0, padx=10, pady=10, sticky="e")
#     type_entry = ttk.Combobox(reminder_frame, values=["Test", "Appointment", "Medication"], width=28)
#     type_entry.grid(row=1, column=1, padx=10, pady=10)
#
#     tk.Label(reminder_frame, text="Date:").grid(row=2, column=0, padx=10, pady=10, sticky="e")
#     date_entry = DateEntry(reminder_frame, date_pattern='yyyy-mm-dd')
#     date_entry.grid(row=2, column=1, padx=10, pady=10)
#
#     def save_reminder():
#         reminder = {
#             "title": title_entry.get().strip(),
#             "type": type_entry.get().strip(),
#             "date": date_entry.get_date().strftime("%Y-%m-%d")
#         }
#
#         try:
#             if not os.path.exists("reminders.json"):
#                 with open("reminders.json", "w") as f:
#                     json.dump([], f)
#             with open("reminders.json", "r") as f:
#                 data = json.load(f)
#             data.append(reminder)
#             with open("reminders.json", "w") as f:
#                 json.dump(data, f, indent=4)
#
#             messagebox.showinfo("Success", "Reminder scheduled successfully!")
#             msg = (
#                 f"✅ Hi {username}, your {reminder['type'].lower()} reminder has been scheduled.\n\n"
#                 f"• Title: {reminder['title']}\n"
#                 f"• Date: {reminder['date']}"
#             )
#             send_telegram_message(msg)
#
#         except Exception as e:
#             messagebox.showerror("Error", f"Failed to save reminder: {e}")
#
#     tk.Button(reminder_frame, text="💾 Schedule Reminder", command=save_reminder, bg="#4CAF50", fg="white").grid(row=3, column=1, pady=20, sticky="e")
#
#     root.mainloop()
