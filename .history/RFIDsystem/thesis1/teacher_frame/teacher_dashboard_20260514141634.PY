import tkinter as tk
from tkinter import messagebox

from teacher_frame.teacher_classroom import TeacherClassroomFrame
from teacher_frame.teacher_download_info import TeacherDownloadFrame


# Hover effect
def add_hover_effect(widget, hover_bg, default_bg):
    widget.bind("<Enter>", lambda e: widget.config(bg=hover_bg))
    widget.bind("<Leave>", lambda e: widget.config(bg=default_bg))


class TeacherDashboard(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)

        self.controller = controller
        self.user_data = {}
        self.username = "Teacher"

        self.configure(bg="#e0f7fa")

        self.current_frame = None
        self.menu_buttons = {}
        self.active_btn = None  # ✅ track active button

        # ================= SIDEBAR =================
        self.sidebar = tk.Frame(self, width=250, bg="#00acc1")
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y)
        self.sidebar.pack_propagate(False)

        tk.Label(
            self.sidebar,
            text="TEACHER PANEL",
            bg="#00acc1",
            fg="white",
            font=("Arial", 16, "bold")
        ).pack(pady=20)

        # MENU BUTTONS
        self.create_menu_button("My Classroom", TeaxClassroomFrame)
        self.create_menu_button("Download Logs", TeacherDownloadFrame)

        # ================= MAIN AREA =================
        self.main_area = tk.Frame(self, bg="#e0f7fa")
        self.main_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # ================= TOP BAR =================
        self.topbar = tk.Frame(self.main_area, height=60, bg="#26c6da")
        self.topbar.pack(fill="x")

        self.title_label = tk.Label(
            self.topbar,
            text="TEACHER DASHBOARD",
            bg="#26c6da",
            fg="white",
            font=("Arial", 16, "bold")
        )
        self.title_label.pack(side="left", padx=20)

        self.welcome_label = tk.Label(
            self.topbar,
            text="Welcome!",
            bg="#26c6da",
            fg="white",
            font=("Arial", 11)
        )
        self.welcome_label.pack(side="left", padx=10)

        logout_btn = tk.Button(
            self.topbar,
            text="Logout",
            bg="#ff6b6b",
            fg="white",
            font=("Arial", 11, "bold"),
            command=self.logout
        )
        logout_btn.pack(side="right", padx=20, pady=10)

        add_hover_effect(logout_btn, "#e63946", "#ff6b6b")

    # ================= LOAD USER =================
    def load_user(self, user_data):
        self.user_data = user_data
        self.username = user_data.get("username", "Teacher")

        # Update UI
        self.title_label.config(text=f"TEACHER DASHBOARD - {self.username.upper()}")
        self.welcome_label.config(text=f"Welcome, {self.username}")

        # Open default page
        self.open_frame(ClassroomFrame)

    # ================= SWITCH FRAME =================
    def open_frame(self, frame_class):
        try:
            # Destroy old frame
            if self.current_frame:
                self.current_frame.destroy()

            # Create new frame
            frame = frame_class(self.main_area, self.controller)

            # Pass user data if supported
            if hasattr(frame, "load_user"):
                frame.load_user(self.user_data)

            frame.pack(fill="both", expand=True)
            self.current_frame = frame

            # Update active button
            self.update_active_button(frame_class)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to open {frame_class.__name__}\n{e}")

    # ================= BUTTON UI CONTROL =================
    def update_active_button(self, frame_class):
        for btn, cls in self.menu_buttons.items():
            if cls == frame_class:
                btn.config(bg="#007c91")  # darker active color
                self.active_btn = btn
            else:
                btn.config(bg="#00acc1")

    # ================= CREATE MENU BUTTON =================
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

    # ================= LOGOUT =================
    def logout(self):
        confirm = messagebox.askyesno("Logout", "Are you sure you want to log out?")
        if confirm:
            self.controller.logout()
            messagebox.showinfo("Logout", "You have been logged out.")