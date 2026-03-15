import tkinter as tk
from tkinter import messagebox  # Added for logout notification

from frames.history_log import RFIDHistory
from frames.report import Report
from frames.account import Account
from frames.teacher_record import TeacherRecord
from frames.student_record import StudentRecord
from frames.fetcher_record import FetcherRecord
from frames.rfid_registration import RfidRegistration
from frames.Classroom import ClassroomFrame
from frames.overrride import OverrideFrame
from frames.adminoverride import AdminOverrideFrame
from frames.admin_record import AdminRecord

# Reusable hover effect
def add_hover_effect(widget, hover_bg, default_bg):
    widget.bind("<Enter>", lambda e: widget.config(bg=hover_bg))
    widget.bind("<Leave>", lambda e: widget.config(bg=default_bg))

class MainDashboard(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.user_data = getattr(self.controller, "current_user", {"role": "Teacher", "username": "User"})
        self.role = self.user_data.get("role", "Teacher")
        
        self.configure(bg="#e0f7fa")
        self.pack(fill="both", expand=True)

        self.current_frame = None
        self.menu_buttons = {}

        # ================= SIDEBAR =================
        self.sidebar = tk.Frame(self, width=250, bg="#00acc1")
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y)
        self.sidebar.pack_propagate(False)

        tk.Label(
            self.sidebar,
            text="RFID MANAGEMENT",
            bg="#00acc1",
            fg="white",
            font=("Arial", 16, "bold")
        ).pack(pady=20)

        # ================= ROLE-BASED MENU BUTTONS =================
        # Logic: Admins see everything. Teachers only see Classroom and Account.
        
        if self.role == "Admin":
            self.create_menu_button("Student Record", StudentRecord)
            self.create_menu_button("Teacher Record", TeacherRecord)
            self.create_menu_button("Fetcher Record", FetcherRecord)
            self.create_menu_button("Admin Record", AdminRecord)
            self.create_menu_button("Assign Fetcher to Student", RfidRegistration)
            self.create_menu_button("Admin Override Card", AdminOverrideFrame)
            self.create_menu_button("Teacher Override Card", OverrideFrame)
            self.create_menu_button("History Log", RFIDHistory)
            self.create_menu_button("Reports", Report)
            self.create_menu_button("Account Settings", Account)
        else:
            # Teacher Role Restriction
            self.create_menu_button("My Classroom", ClassroomFrame)

        # ================= MAIN AREA =================
        self.main_area = tk.Frame(self, bg="#e0f7fa")
        self.main_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # ================= TOP BAR =================
        self.topbar = tk.Frame(self.main_area, height=50, bg="#26c6da", bd=2, relief="groove")
        self.topbar.pack(fill="x")

        # Dynamic Title based on role
        panel_title = "SYSTEM ADMINISTRATION" if self.role == "Admin" else f"TEACHER PANEL: {self.user_data.get('username').upper()}"
        
        tk.Label(
            self.topbar,
            text=f"CAINTA CATHOLIC COLLEGE - {panel_title}",
            bg="#26c6da",
            fg="white",
            font=("Arial", 14, "bold")
        ).pack(side="left", padx=20)

        logout_btn = tk.Button(
            self.topbar,
            text="Logout",
            bg="#ff6b6b",
            fg="white",
            font=("Arial", 12, "bold"),
            relief="raised",
            bd=2,
            padx=15,
            pady=5,
            command=self.logout
        )
        logout_btn.pack(side="right", padx=20, pady=8)
        add_hover_effect(logout_btn, "#e63946", "#ff6b6b")

        # ================= OPEN DEFAULT FRAME =================
        # Logic: If Admin, open Student Record. If Teacher, open Classroom Frame.
        if self.role == "Admin":
            self.open_frame(StudentRecord)
        else:
            self.open_frame(ClassroomFrame)

    def open_frame(self, frame_class):
        try:
            if self.current_frame:
                self.current_frame.destroy()

            # 1. Create the new frame
            self.current_frame = frame_class(self.main_area, self.controller)
            self.current_frame.pack(fill="both", expand=True)


            frame_name = frame_class.__name__
        
            # 3. Highlight menu button
            for btn, cls in self.menu_buttons.items():
                btn.config(bg="#00838f" if cls == frame_class else "#00acc1")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open {frame_class.__name__}:\n{e}")

    def create_menu_button(self, text, frame_class):
        btn = tk.Button(
            self.sidebar,
            text=text,
            bg="#00acc1",
            fg="white",
            anchor="w",
            relief="flat",
            padx=20,
            pady=15,
            font=("Arial", 12, "bold"),
            command=lambda: self.open_frame(frame_class)
        )
        btn.pack(fill="x", pady=2)
        add_hover_effect(btn, "#00838f", "#00acc1")
        self.menu_buttons[btn] = frame_class

    # ================= UPDATED LOGOUT FUNCTION =================
    def logout(self):
        # 1. Ask for confirmation
        confirm = messagebox.askyesno("Logout", "Are you sure you want to log out?")
        if confirm:
            # 2. Clear the variable in the main app
            self.controller.logout()
            
            # 3. Inform the user
            messagebox.showinfo("Logout", "You have been logged out.")