import tkinter as tk
from tkinter import messagebox, ttk
import os
import sys
from datetime import datetime
# =================== PATH SETUP ===================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from utils.database import db_connect


class Account(tk.Frame):
    def __init__(self, parent, controller=None):
        super().__init__(parent, bg="#b2e5ed")
        self.controller = controller

        # Header Section
        header = tk.Frame(self, bg="#0047AB", height=90)
        header.pack(fill="x")
        tk.Label(
            header,
            text="USER MANAGEMENT",
            font=("Arial", 22, "bold"),
            bg="#0047AB",
            fg="white"
        ).pack(side="left", padx=30, pady=25)

        # Content Container
        content = tk.Frame(self, bg="#b2e5ed")
        content.pack(fill="both", expand=True, padx=20, pady=20)
        content.columnconfigure(0, weight=3)
        content.columnconfigure(1, weight=0)
        content.rowconfigure(1, weight=1)

        # Search Bar Area
        search_frame = tk.Frame(content, bg="#b2e5ed")
        search_frame.grid(row=0, column=0, sticky="w", pady=(0, 10))

        self.search_var = tk.StringVar()
        self.search_entry = tk.Entry(
            search_frame, textvariable=self.search_var, width=35, font=("Arial", 12)
        )
        self.search_entry.pack(side="left", padx=(0, 5), ipady=3)

        tk.Button(
            search_frame,
            text="Search User",
            bg="#0047AB",
            fg="white",
            command=self.search_account
        ).pack(side="left")
        tk.Button(
            search_frame,
            text="Refresh",
            command=self.load_accounts
        ).pack(side="left", padx=5)

        # Account Table
        table_frame = tk.Frame(content, bg="white", bd=1, relief="solid")
        table_frame.grid(row=1, column=0, sticky="nsew")

        columns = ("id", "employee_id", "username", "created", "role")
        self.account_table = ttk.Treeview(table_frame, columns=columns, show="headings")

        for col in columns:
            self.account_table.heading(col, text=col.title())
            self.account_table.column(col, anchor="center")

        self.account_table.pack(fill="both", expand=True)

        # Table Styling
        style = ttk.Style()
        style.theme_use("default")
        style.configure(
            "Treeview",
            font=("Arial", 10),
            rowheight=25
        )
        style.configure(
            "Treeview.Heading",
            font=("Arial", 10, "bold"),
            background="#f0f0f0",
            foreground="#000000"
        )
        style.map("Treeview.Heading", background=[('active', '#d9d9d9')])

        # Sidebar Buttons
        btn_frame = tk.Frame(content, bg="#b2e5ed")
        btn_frame.grid(row=1, column=1, sticky="n", padx=(20, 0))

        button_specs = [
            ("CHANGE PASSWORD", "#2196F3", self.change_password),
            ("DELETE ACCOUNT", "#F44336", self.delete_account)
        ]

        for text, color, cmd in button_specs:
            tk.Button(
                btn_frame,
                text=text,
                width=18,
                height=2,
                bg=color,
                fg="white",
                font=("Arial", 10, "bold"),
                command=cmd
            ).pack(pady=5)

        self.load_accounts()

    def load_accounts(self):
        """Fetch all users from DB safely."""
        self.account_table.delete(*self.account_table.get_children())
        try:
            with db_connect() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT id, employee_id, username, created_at, role FROM users ORDER BY id DESC"
                )
                for row in cursor.fetchall():
                    # Convert datetime to string for display
                    row = list(row)
                    if isinstance(row[3], datetime):
                        row[3] = row[3].strftime("%Y-%m-%d %H:%M:%S")
                    self.account_table.insert("", "end", values=row)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load accounts: {e}")

    def search_account(self):
        query = self.search_var.get().strip()
        if not query:
            self.load_accounts()
            return

        self.account_table.delete(*self.account_table.get_children())
        try:
            with db_connect() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT id, employee_id, username, created_at, role FROM users WHERE username LIKE %s",
                    (f"%{query}%",)
                )
                for row in cursor.fetchall():
                    row = list(row)
                    if isinstance(row[3], datetime):
                        row[3] = row[3].strftime("%Y-%m-%d %H:%M:%S")
                    self.account_table.insert("", "end", values=row)
        except Exception as e:
            messagebox.showerror("Search Error", str(e))

    
    def change_password(self):
        from frames.change_password import ChangePasswordWindow  # import here to avoid circular import
        selected = self.account_table.focus()
        if not selected:
            messagebox.showwarning("Selection Required", "Please select an account to modify.")
            return
        user_data = self.account_table.item(selected, "values")
        ChangePasswordWindow(self, user_data)
        

    def delete_account(self):
        selected = self.account_table.focus()
        if not selected:
            messagebox.showwarning("Selection Required", "Please select an account to delete.")
            return

        user_data = self.account_table.item(selected, "values")
        user_id, username = user_data[0], user_data[2]  # Corrected index: username is 2

        if self.controller and getattr(self.controller, "current_user", None):
            current_username = self.controller.current_user.get("username")

            if username == current_username:
                messagebox.showerror(
                    "Action Denied",
                    "You cannot delete your own account while logged in."
                )
                return

        if messagebox.askyesno("Confirm Deletion", f"Are you sure you want to delete account: {username}?\nThis action cannot be undone."):
            try:
                with db_connect() as conn:
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM users WHERE id=%s", (user_id,))
                    conn.commit()
                messagebox.showinfo("Success", "Account removed successfully.")
                self.load_accounts()
            except Exception as e:
                messagebox.showerror("Database Error", str(e))