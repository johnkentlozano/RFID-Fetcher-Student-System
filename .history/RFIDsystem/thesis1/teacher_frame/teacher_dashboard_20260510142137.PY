import tkinter as tk
from tkinter import messagebox

# Import teacher-only frames
from teacher_frame.teacher_classroom import ClassroomFrame
from teacher_frame.teacher_download_info import TeacherDownloadframe
from teacher


# Hover effect
def add_hover_effect(widget, hover_bg, default_bg):
    widget.bind("<Enter>", lambda e: widget.config(bg=hover_bg))
    widget.bind("<Leave>", lambda e: widget.config(bg=default_bg))


class TeacherDashboard(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)

        self.controller = controller
        self.user_data = getattr(self.controller, "current_user", {"username": "Teacher"})
        self.username = self.user_data.get("username", "Teacher")

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
            text="TEACHER PANEL",
            bg="#00acc1",
            fg="white",
            font=("Arial", 16, "bold")
        ).pack(pady=20)

        # ✅ TEACHER MENU ONLY
        self.create_menu_button("My Classroom", ClassroomFrame)
        # self.create_menu_button("Download Logs", TeacherDownload)  # add later
        self.create_menu_button("Account Settings", Account)

        # ================= MAIN AREA =================
        self.main_area = tk.Frame(self, bg="#e0f7fa")
        self.main_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # ================= TOP BAR =================
        self.topbar = tk.Frame(self.main_area, height=50, bg="#26c6da", bd=2, relief="groove")
        self.topbar.pack(fill="x")

        tk.Label(
            self.topbar,
            text=f"TEACHER DASHBOARD - {self.username.upper()}",
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
            command=self.logout
        )
        logout_btn.pack(side="right", padx=20, pady=8)
        add_hover_effect(logout_btn, "#e63946", "#ff6b6b")

        # ================= DEFAULT FRAME =================
        self.open_frame(ClassroomFrame)

    # ================= SWITCH FRAME =================
    def open_frame(self, frame_class):
        try:
            if self.current_frame:
                self.current_frame.destroy()

            self.current_frame = frame_class(self.main_area, self.controller)
            self.current_frame.pack(fill="both", expand=True)

            # Highlight button
            for btn, cls in self.menu_buttons.items():
                btn.config(bg="#00838f" if cls == frame_class else "#00acc1")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to open {frame_class.__name__}\n{e}")

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