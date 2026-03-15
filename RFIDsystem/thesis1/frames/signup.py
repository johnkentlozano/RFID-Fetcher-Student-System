from utils.database import db_connect
from utils.security import hash_password, is_strong_password
from utils.helpers import add_hover_effect, get_image_path
from PIL import ImageTk, Image
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox

class SignUpFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#F5F5F5")
        self.controller = controller
        self.left_image()
        self.signup_panel()

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

    def signup_panel(self):
        panel = tk.Frame(self, width=420, height=650, bg="white", bd=0, highlightthickness=1, highlightbackground="#DDDDDD")
        panel.place(relx=0.78, rely=0.5, anchor="center")
        panel.pack_propagate(False)

        tk.Label(panel, text="Join Us", font=("Helvetica", 24, "bold"),
                 bg="white", fg="#0047AB").pack(pady=(20, 10))

        form_container = tk.Frame(panel, bg="white")
        form_container.pack(fill="x", padx=40)

        # Pass the new 'alphanumeric' flag to the entry helper
        self.username = self.entry(form_container, "Username", validate_type="alphanumeric")
        self.employee_id = self.entry(form_container, "Employee ID", validate_type="numeric")
        
        # --- Password Field ---
        tk.Label(form_container, text="Password", bg="white", font=("Arial", 9, "bold")).pack(anchor="w")
        pass_frame = tk.Frame(form_container, bg="#F8F9FA", highlightthickness=1, highlightbackground="#CCCCCC")
        pass_frame.pack(fill="x", pady=(2, 10))

        self.password = tk.Entry(pass_frame, font=("Arial", 12), bg="#F8F9FA", bd=0, show="*")
        self.password.pack(side=tk.LEFT, expand=True, fill="x", ipady=6, padx=5)

        self.toggle_pass = tk.Button(pass_frame, text="👁️", bg="#F8F9FA", bd=0, cursor="hand2",
                             command=lambda: self.toggle_visibility(self.password))
        self.toggle_pass.pack(side=tk.RIGHT, padx=5)

        # --- Confirm Password Field ---
        tk.Label(form_container, text="Confirm Password", bg="white", font=("Arial", 9, "bold")).pack(anchor="w")
        conf_frame = tk.Frame(form_container, bg="#F8F9FA", highlightthickness=1, highlightbackground="#CCCCCC")
        conf_frame.pack(fill="x", pady=(2, 10))

        self.confirm = tk.Entry(conf_frame, font=("Arial", 12), bg="#F8F9FA", bd=0, show="*")
        self.confirm.pack(side=tk.LEFT, expand=True, fill="x", ipady=6, padx=5)

        self.toggle_conf = tk.Button(conf_frame, text="👁️", bg="#F8F9FA", bd=0, cursor="hand2",
                             command=lambda: self.toggle_visibility(self.confirm))
        self.toggle_conf.pack(side=tk.RIGHT, padx=5)
                           
        # ROLE SELECTION DROPDOWN
        tk.Label(form_container, text="Account Role", bg="white", font=("Arial", 9, "bold")).pack(anchor="w")
        self.role_var = tk.StringVar(value="Teacher")
        self.role_dropdown = ttk.Combobox(form_container, textvariable=self.role_var, state="readonly", font=("Arial", 11))
        self.role_dropdown['values'] = ("Teacher", "Admin")
        self.role_dropdown.pack(fill="x", pady=(2, 10))

        req_frame = tk.Frame(form_container, bg="white")
        req_frame.pack(fill="x", pady=5)
        
        self.pw_reqs = {
            "length": tk.Label(req_frame, text="• 8+ characters", fg="red", bg="white", font=("Arial", 8)),
            "upper": tk.Label(req_frame, text="• Uppercase letter", fg="red", bg="white", font=("Arial", 8)),
            "digit": tk.Label(req_frame, text="• Number", fg="red", bg="white", font=("Arial", 8)),
            "special": tk.Label(req_frame, text="• Special character", fg="red", bg="white", font=("Arial", 8))
        }

        self.pw_reqs["length"].grid(row=0, column=0, sticky="w", padx=5)
        self.pw_reqs["upper"].grid(row=0, column=1, sticky="w", padx=5)
        self.pw_reqs["digit"].grid(row=1, column=0, sticky="w", padx=5)
        self.pw_reqs["special"].grid(row=1, column=1, sticky="w", padx=5)

        self.password.bind("<KeyRelease>", self.validate_password)

        btn_signup = tk.Button(panel, text="CREATE ACCOUNT", bg="#00A86B", fg="white", cursor="hand2",
                        font=("Arial", 12, "bold"), bd=0, command=self.signup)
        btn_signup.pack(fill="x", padx=40, pady=(15, 10), ipady=10)
        add_hover_effect(btn_signup, "#007A4D", "#00A86B")

        back = tk.Button(panel, text="Already have an account? Login", bg="white", fg="#666666",
                         bd=0, font=("Arial", 9), cursor="hand2",
                         command=lambda: self.controller.show_frame("LoginFrame"))
        back.pack()

    def entry(self, panel, text, hide=False, validate_type=None):
        tk.Label(panel, text=text, bg="white", font=("Arial", 9, "bold")).pack(anchor="w")
    

        e = tk.Entry(panel, font=("Arial", 12), bg="#F8F9FA", bd=0, 
                 highlightthickness=1, highlightbackground="#CCCCCC", 
                 show="*" if hide else "")
    
   
        if validate_type == "alphanumeric":
            vcmd = (self.register(self.validate_username), '%P')
            e.config(validate="key", validatecommand=vcmd)
            
        if validate_type == "numeric":
            vcmd = (self.register(self.validate_employeed_id), '%P')
            e.config(validate="key", validatecommand=vcmd)
        
        e.pack(fill="x", ipady=6, pady=(2, 10))
        return e

    def toggle_visibility(self, entry_widget):
        if entry_widget.cget("show") == "*":
            entry_widget.config(show="")
        else:
            entry_widget.config(show="*")

    def validate_password(self, event=None):
        pw = self.password.get()

        self.pw_reqs["length"].config(fg="green" if len(pw) >= 8 else "red")
        self.pw_reqs["upper"].config(fg="green" if any(c.isupper() for c in pw) else "red")
        self.pw_reqs["digit"].config(fg="green" if any(c.isdigit() for c in pw) else "red")
        self.pw_reqs["special"].config(
        fg="green" if any(not c.isalnum() for c in pw) else "red"
    )

    def signup(self):
        user = self.username.get().strip()
        emp_id = self.employee_id.get().strip()
        pw = self.password.get()
        cpw = self.confirm.get()
        role = self.role_var.get()
        

        if not user or not pw or not emp_id:
            messagebox.showerror("Error", "All fields required")
            return

        if pw != cpw:
            messagebox.showerror("Error", "Passwords do not match")
            return

        if not is_strong_password(pw):
            messagebox.showerror("Error", "Password too weak")
            return

        hashed = hash_password(pw)

        try:
            with db_connect() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT * FROM users WHERE employee_id=%s", (emp_id,))
                    if cur.fetchone():
                        messagebox.showerror("Error", "Employee ID exists")
                        return

                    cur.execute(
                        "INSERT INTO users (username, password, employee_id, role) VALUES (%s, %s, %s, %s)",
                        (user, hashed, emp_id, role)
                    )
                    conn.commit()

            messagebox.showinfo("Success", f"Account created as {role}")
            self.controller.show_frame("LoginFrame")

        except Exception as e:
            messagebox.showerror("Error", f"Database error: {e}")
            
    def validate_username(self, text):
        return text.isalnum() or text == ""
    
    def validate_employeed_id(self, text):
        return text.isdigit() or text == ""