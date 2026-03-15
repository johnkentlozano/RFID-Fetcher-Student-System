
import tkinter as tk
from tkinter import messagebox
from utils.security import hash_password, is_strong_password
from utils.database import db_connect


class ForgotPasswordFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#F5F5F5")
        self.controller = controller
        self.forgot_panel()
        
    def forgot_panel(self):
        panel = tk.Frame(self, width=420, height=480, bg="white", bd=0, highlightthickness=1, highlightbackground="#DDDDDD")
        panel.place(relx=0.5, rely=0.5, anchor="center") 
        panel.pack_propagate(False)

        tk.Label(panel, text="Reset Password", font=("Helvetica", 20, "bold"), 
                 bg="white", fg="#0047AB").pack(pady=30)

        container = tk.Frame(panel, bg="white")
        container.pack(fill="x", padx=40)

        tk.Label(container, text="Username", bg="white", font=("Arial", 9, "bold")).pack(anchor="w")
        self.username = tk.Entry(container, font=("Arial", 12), bg="#F8F9FA", bd=0, highlightthickness=1, highlightbackground="#CCCCCC")
        self.username.pack(fill="x", ipady=8, pady=(2, 15))

        tk.Label(container, text="Employee ID", bg="white", font=("Arial", 9, "bold")).pack(anchor="w")
        self.employee_id = tk.Entry(container, font=("Arial", 12), bg="#F8F9FA", bd=0, highlightthickness=1, highlightbackground="#CCCCCC")
        self.employee_id.pack(fill="x", ipady=8, pady=(2, 15))

        tk.Label(container, text="New Password", bg="white", font=("Arial", 9, "bold")).pack(anchor="w")
        self.new_pw = tk.Entry(container, font=("Arial", 12), bg="#F8F9FA", bd=0, highlightthickness=1, highlightbackground="#CCCCCC", show="*")
        self.new_pw.pack(fill="x", ipady=8, pady=(2, 15))

        btn = tk.Button(panel, text="UPDATE PASSWORD", bg="#0047AB", fg="white", cursor="hand2",
                        font=("Arial", 11, "bold"), bd=0, command=self.reset_password)
        btn.pack(fill="x", padx=40, pady=20, ipady=10)

        back = tk.Button(panel, text="Cancel", bg="white", fg="#666666", bd=0, cursor="hand2",
                         command=lambda: self.controller.show_frame("LoginFrame"))
        back.pack()

    def reset_password(self):
        user, emp_id, new_pw = self.username.get().strip(), self.employee_id.get().strip(), self.new_pw.get()

        if not user or not emp_id or not new_pw:
            messagebox.showerror("Error", "Please fill all fields")
            return
        
        if not is_strong_password(new_pw):
            messagebox.showerror("Error", "New password is too weak!")
            return

        hashed = hash_password(new_pw)


        try:
            with db_connect() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT * FROM users WHERE username=%s AND employee_id=%s", (user, emp_id))
                    if cur.fetchone():
                        cur.execute("UPDATE users SET password=%s WHERE username=%s AND employee_id=%s", 
                                    (hashed, user, emp_id))
                        conn.commit()
                        messagebox.showinfo("Success", "Password updated!")
                        self.controller.show_frame("LoginFrame")
                    else:
                        messagebox.showerror("Error", "User details do not match.")
        except Exception as e: 
            messagebox.showerror("Error", f"Database error: {e}")