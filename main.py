import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
import csv
import os


def load_users():
    users = {}
    try:
        if not os.path.exists("users.csv"):
            raise FileNotFoundError

        with open("users.csv", "r") as file:
            reader = csv.DictReader(file)
            for row in reader:
                if not all(key in row for key in ["username", "password", "role"]):
                    raise ValueError("Invalid users.csv format")
                users[row["username"]] = {
                    "password": row["password"],
                    "role": row["role"]
                }
        return users
    except FileNotFoundError:
        messagebox.showerror("Critical Error", "users.csv not found!")
        return {}
    except Exception as e:
        messagebox.showerror("Error", f"Failed to load users: {str(e)}")
        return {}


def login():
    username = username_entry.get().strip()
    password = password_entry.get().strip()

    if not username or not password:
        messagebox.showwarning("Validation", "Username and password are required")
        return

    if username in users and users[username]["password"] == password:
        role = users[username]["role"]
        messagebox.showinfo("Success", f"Welcome {username} ({role})")
        root.destroy()

        if role == "admin":
            import dashboard_admin as dashboard
        else:
            import dashboard_user as dashboard

        dashboard.show_dashboard(username)
    else:
        messagebox.showerror("Failed", "Invalid credentials")


# Main UI
if __name__ == "__main__":
    users = load_users()

    root = tk.Tk()
    root.title("Health Analyzer Login")
    root.geometry("400x320")
    root.resizable(False, False)

    # Colors (monochromatic palette based on #32de84)
    main_bg = "#e6f9f0"        # very light green tint
    frame_bg = "#c0f2dc"       # light green
    entry_bg = "#ffffff"
    accent = "#32de84"         # main accent green
    accent_dark = "#28c673"    # darker shade for buttons
    text_color = "#1f5131"

    root.configure(bg=main_bg)

    # Header
    header = tk.Label(root, text="Health Analyzer", font=("Segoe UI", 18, "bold"),
                      bg=main_bg, fg=accent_dark)
    header.pack(pady=20)

    # Form frame
    form_frame = tk.Frame(root, bg=frame_bg, bd=2, relief="groove")
    form_frame.pack(padx=30, pady=10, fill="both", expand=False)

    tk.Label(form_frame, text="Username:", font=("Segoe UI", 11),
             bg=frame_bg, fg=text_color).grid(row=0, column=0, sticky="e", padx=10, pady=10)
    username_entry = tk.Entry(form_frame, width=30, bg=entry_bg, relief="solid")
    username_entry.grid(row=0, column=1, padx=10, pady=10)

    tk.Label(form_frame, text="Password:", font=("Segoe UI", 11),
             bg=frame_bg, fg=text_color).grid(row=1, column=0, sticky="e", padx=10, pady=10)
    password_entry = tk.Entry(form_frame, show="*", width=30, bg=entry_bg, relief="solid")
    password_entry.grid(row=1, column=1, padx=10, pady=10)

    # Login button
    login_btn = tk.Button(root, text="🔐 Login", command=login,
                          bg=accent, fg="white", activebackground=accent_dark,
                          font=("Segoe UI", 11, "bold"), relief="flat", width=15)
    login_btn.pack(pady=20)

    root.mainloop()
