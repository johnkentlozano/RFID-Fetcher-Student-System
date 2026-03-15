import tkinter as tk
from tkinter import messagebox, ttk
import os
import sys
from datetime import datetime

# =================== PATH SETUP ===================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

try:
    from utils.database import db_connect
except ImportError:
    def db_connect():
        raise ImportError("utils.database.db_connect not found. Please check your path setup.")

class Account(tk.Frame):
    def __init__(self, parent, controller=None):
        super().__init__(parent, bg="#b2e5ed")
        self.controller = controller


        header = tk.Frame(self, bg="#0047AB", height=90)
        header.pack(fill="x")
        tk.Label(
            header,
            text="USER MANAGEMENT",
            font=("Arial", 22, "bold"),
            bg="#0047AB",
            fg="white"
        ).pack(side="left", padx=30, pady=25)

        content = tk.Frame(self, bg="#b2e5ed")
        content.pack(fill="both", expand=True, padx=20, pady=20)
        content.columnconfigure(0, weight=3)
        content.columnconfigure(1, weight=0)
        content.rowconfigure(1, weight=1)

        
        search_frame = tk.Frame(content, bg="#b2e5ed")
        search_frame.grid(row=0, column=0, sticky="w", pady=(0, 10))

        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *args: self.search_account())
        
        self.search_entry = tk.Entry(
            search_frame, textvariable=self.search_var, width=35, font=("Arial", 12)
        )
        self.search_entry.pack(side="left", padx=(0, 5), ipady=3)

        tk.Button(search_frame,text="Refresh List",bg="#0047AB",fg="white", command=self.load_accounts).pack(side="left", padx=5)

        table_frame = tk.Frame(content, bg="white", bd=1, relief="solid")
        table_frame.grid(row=1, column=0, sticky="nsew")

        columns = ("id", "employee_id", "username", "created", "role")
        self.account_table = ttk.Treeview(table_frame, columns=columns, show="headings")

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.account_table.yview)
        self.account_table.configure(yscrollcommand=scrollbar.set)


        headers = {
            "id": "ID",
            "employee_id": "Employee ID",
            "username": "Username",
            "created": "Created At",
            "role": "Role"
        }

        for col in columns:
            self.account_table.heading(col, text=headers[col])
            self.account_table.column(col, anchor="center", width=100)
    
        self.account_table.column("id", width=50)
        self.account_table.column("username", width=150)
        self.account_table.column("created", width=180)

        scrollbar.pack(side="right", fill="y")
        self.account_table.pack(side="left", fill="both", expand=True)

        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", font=("Arial", 10), rowheight=30)
        style.configure("Treeview.Heading", font=("Arial", 10, "bold"), background="#f0f0f0")
        style.map("Treeview", background=[('selected', '#0047AB')])

        btn_frame = tk.Frame(content, bg="#b2e5ed")
        btn_frame.grid(row=1, column=1, sticky="n", padx=(20, 0))

        button_specs = [
            ("CHANGE PASSWORD", "#2196F3", self.change_password),
            ("DELETE ACCOUNT", "#F44336", self.delete_account)
        ]

        for text, color, cmd in button_specs:
            tk.Button( btn_frame,text=text,width=18, height=2, bg=color,fg="white",font=("Arial", 10, "bold"),command=cmd,cursor="hand2"
            ).pack(pady=5)
        self.load_accounts()

    def fetch_data(self, filter_text=None):
        results = []
        try:
            with db_connect() as conn:
                cursor = conn.cursor()
                if filter_text:
                    clean_text = filter_text.replace('%', '\\%').replace('_', '\\_')
                
                    sql = """SELECT id, employee_id, username, created_at, role 
                        FROM users 
                        WHERE (username LIKE %s ESCAPE '|') 
                        OR (employee_id LIKE %s ESCAPE '|') 
                        ORDER BY id DESC"""
                        
                    clean_text = filter_text.replace('|', '||').replace('%', '|%').replace('_', '|_')
                    cursor.execute(sql, (f"%{clean_text}%", f"%{clean_text}%"))
                else:
                    cursor.execute("SELECT id, employee_id, username, created_at, role FROM users ORDER BY id DESC")
            
                for row in cursor.fetchall():
                    row = list(row)
                    if isinstance(row[3], datetime):
                        row[3] = row[3].strftime("%Y-%m-%d %H:%M")
                    results.append(row)
        except Exception as e:
            messagebox.showerror("Database Error", f"Could not retrieve data:\n{e}")
        return results

    def load_accounts(self):
        self.account_table.delete(*self.account_table.get_children())
        data = self.fetch_data()
        for row in data:
            self.account_table.insert("", "end", values=row)

    def search_account(self):
        query = self.search_var.get().strip()
        self.account_table.delete(*self.account_table.get_children())
        data = self.fetch_data(query if query else None)
        for row in data:
            self.account_table.insert("", "end", values=row)

    def change_password(self):
        # Local import to prevent circular dependency
        from frames.change_password import ChangePasswordWindow
        selected = self.account_table.focus()
        if not selected:
            messagebox.showwarning("Selection Required", "Please select a user from the table.")
            return
        
        user_data = self.account_table.item(selected, "values")
        ChangePasswordWindow(self, user_data)

    def delete_account(self):
        selected_item = self.account_table.selection()
        if not selected_item:
            messagebox.showwarning("Selection Required", "Please select a user to delete.")
            return

        user_data = self.account_table.item(selected_item, "values")
        
        if not user_data or len(user_data) < 3:
            messagebox.showerror("Error", "Could not retrieve user data.")
            return

        user_id = user_data[0]
        username = user_data[2] 

        current_logged_in_name = self.controller.current_user.get("username") if self.controller.current_user else None

        if username == current_logged_in_name:
            messagebox.showerror("Action Denied", "Security Violation: You cannot delete your own account.")
            return

        if messagebox.askyesno("Confirm Deletion", f"Are you sure you want to delete '{username}'?"):
            try:
                with db_connect() as conn:
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM users WHERE id=%s", (user_id,))
                    conn.commit()
                messagebox.showinfo("Success", "Account successfully deleted.")
                self.load_accounts()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete record: {e}")