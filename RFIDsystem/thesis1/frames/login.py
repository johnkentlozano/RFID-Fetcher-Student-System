import tkinter as tk
from tkinter import messagebox
from PIL import ImageTk, Image
import sys, os
import bcrypt
# Ensure utility imports work
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)
from utils.database import db_connect
from utils.validators import validate_required
from utils.helpers import add_hover_effect, get_image_path # make sure this exists

class LoginFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#F5F5F5")
        self.controller = controller
        self.failed_attempts = 0
        self.left_image()
        self.login_panel()

    # ---------------- LEFT IMAGE ----------------
    def left_image(self):
        left = tk.Frame(self, width=675, height=700, bg="#E0E0E0")
        left.pack(side=tk.LEFT, fill=tk.BOTH)
        left.pack_propagate(False)

        target_file = "ccclogo.jpg"
        img_path = get_image_path(target_file)

        if img_path:
            try:
                img = Image.open(img_path).resize((675, 700), Image.Resampling.LANCZOS)
                self.photo = ImageTk.PhotoImage(img)
                img_label = tk.Label(left, image=self.photo, bg="#E0E0E0")
                img_label.image = self.photo
                img_label.pack(fill=tk.BOTH, expand=True)
            except Exception as e:
                tk.Label(left, text=f"Error: {e}", fg="red").pack(expand=True)
        else:
            tk.Label(left, text=f"COULD NOT FIND: {target_file}",
                     fg="red", bg="#E0E0E0", font=("Arial", 9)).pack(expand=True)

    # ---------------- LOGIN PANEL ----------------
    def login_panel(self):
        panel = tk.Frame(self, width=420, height=550, bg="white", bd=0,
                         highlightthickness=1, highlightbackground="#DDDDDD")
        panel.place(relx=0.78, rely=0.5, anchor="center")
        panel.pack_propagate(False)

        tk.Label(panel, text="Welcome Back!", font=("Helvetica", 24, "bold"),
                 bg="white", fg="#0047AB").pack(pady=(40, 30))

        input_container = tk.Frame(panel, bg="white")
        input_container.pack(fill="x", padx=40)

        # Username
        tk.Label(input_container, text="Username", bg="white", font=("Arial", 10, "bold")).pack(anchor="w")
        self.username = tk.Entry(input_container, font=("Arial", 12), bg="#F8F9FA", bd=0,
                                 highlightthickness=1, highlightbackground="#CCCCCC")
        self.username.pack(fill="x", ipady=8, pady=(5, 15))

        # Employee ID
        tk.Label(input_container, text="Employee ID", bg="white", font=("Arial", 10, "bold")).pack(anchor="w")
        self.employee_id = tk.Entry(input_container, font=("Arial", 12), bg="#F8F9FA", bd=0,
                                    highlightthickness=1, highlightbackground="#CCCCCC")
        self.employee_id.pack(fill="x", ipady=8, pady=(5, 15))

        # Password
        tk.Label(input_container, text="Password", bg="white", font=("Arial", 10, "bold")).pack(anchor="w")
        pass_frame = tk.Frame(input_container, bg="#F8F9FA", highlightthickness=1, highlightbackground="#CCCCCC")
        pass_frame.pack(fill="x", pady=(5, 0))

        self.password = tk.Entry(pass_frame, font=("Arial", 12), bg="#F8F9FA", bd=0, show="*")
        self.password.pack(side=tk.LEFT, fill="x", expand=True, ipady=8, padx=5)

        toggle_button = tk.Button(pass_frame, text="👁️", bg="#F8F9FA", bd=0, cursor="hand2",
                                  command=self.password_visibility)
        toggle_button.pack(side=tk.RIGHT, padx=5)

        # Login Button
        btn = tk.Button(panel, text="LOGIN", bg="#0047AB", fg="white", cursor="hand2",
                        font=("Arial", 12, "bold"), bd=0, command=self.login)
        btn.pack(fill="x", padx=40, pady=(30, 10), ipady=10)
        add_hover_effect(btn, "#003380", "#0047AB")
        

        # Footer
        footer_frame = tk.Frame(panel, bg="white")
        footer_frame.pack(fill="x", padx=40)

        su = tk.Button(footer_frame, text="Create Account", font=("Arial", 9), bg="white", fg="#00A86B",
                       bd=0, cursor="hand2", command=lambda: self.controller.show_frame("SignUpFrame"))
        su.pack(side=tk.LEFT)

        forgot_btn = tk.Button(footer_frame,text="Forgot Password?",fg="#666666",bg="white",bd=0,font=("Arial", 9),cursor="hand2",
            command=lambda: self.controller.show_frame("ForgotPasswordFrame")
        )
        forgot_btn.pack(side=tk.RIGHT)

    # ---------------- LOGIN LOGIC ----------------
    def login(self):
        user = self.username.get().strip()
        emp_id = self.employee_id.get().strip()
        pw = self.password.get()

        if not validate_required(user, emp_id, pw):
            messagebox.showerror("Error", "All fields required")
            return

        try:
            with db_connect() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT password, employee_id, role FROM users WHERE username=%s", (user,))
                    result = cur.fetchone()
        except Exception as e:
            messagebox.showerror("Error", f"Database error: {e}")
            return

        if result:
            stored_pw, stored_emp_id, role = result

            if emp_id != str(stored_emp_id):
                messagebox.showerror("Error", "Employee ID is incorrect")
                return

            if not bcrypt.checkpw(pw.encode(), stored_pw.encode()):
                messagebox.showerror("Error", "Password is incorrect")
                return

            user_data = {"username": user, "employee_id": emp_id, "role": role}
            self.controller.login_success(user_data)
        else:
            messagebox.showerror("Error", "Username not found")

    # ---------------- PASSWORD TOGGLE ----------------
    def password_visibility(self):
        if self.password.cget("show") == "*":
            self.password.config(show="")
        else:
            self.password.config(show="*")
            
   