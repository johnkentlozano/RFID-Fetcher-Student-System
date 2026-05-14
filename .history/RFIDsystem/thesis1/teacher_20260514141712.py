import tkinter as tk
from tkinter import messagebox

from teacher_frame.teacher_login import TeacherLoginFrame
from teacher_frame.teacher_signup import TeacherSignUpFrame
from teacher_frame.teacher_classroom import ClassroomFrame
from teacher_frame.forgot_pass_teacher import ForgotPasswordFrame
from teacher_frame.teacher_download_info import TeacherDownloadFrame
from teacher_frame.teacher_dashboard import TeacherDashboard


class TeacherApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Teacher System")
        self.geometry("1200x700")

        self.current_user = None

        container = tk.Frame(self)
        container.pack(fill="both", expand=True)

        container.rowconfigure(0, weight=1)
        container.columnconfigure(0, weight=1)

        self.frames = {}

        # ✅ ALL FRAMES REGISTERED (CORRECT)
        for F in (
            TeacherLoginFrame,
            TeacherSignUpFrame,
            ForgotPasswordFrame,
            TeacherDashboard,
            ClassroomFrame,
            TeacherDownloadFrame
        ):
            frame = F(container, self)
            self.frames[F.__name__] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame("TeacherLoginFrame")

    # ================= SWITCH FRAME =================
    def show_frame(self, name):
        frame = self.frames.get(name)
        if frame:
            frame.tkraise()
        else:
            print(f"[ERROR] Frame not found: {name}")

    # ================= LOGIN SUCCESS =================
    def login_success(self, user_data):
        if user_data.get("role") != "Teacher":
            messagebox.showerror("Access Denied", "Teachers only")
            return

        self.current_user = user_data

        # ✅ DASHBOARD
        dashboard = self.frames.get("TeacherDashboard")
        if dashboard and hasattr(dashboard, "load_user"):
            dashboard.load_user(user_data)

        # ✅ CLASSROOM
        classroom = self.frames.get("TeacherClassroomFrame")
        if classroom and hasattr(classroom, "load_user"):
            classroom.load_user(user_data)

        # ✅ DOWNLOAD FRAME (FIXED)
        download = self.frames.get("TeacherDownloadFrame")
        if download:
            # pass user safely
            download.controller.current_user = user_data

            # ✅ call load_user if exists (important fix)
            if hasattr(download, "load_user"):
                download.load_user(user_data)

        self.show_frame("TeacherDashboard")

    # ================= LOGOUT =================
    def logout(self):
        self.current_user = None
        self.show_frame("TeacherLoginFrame")


if __name__ == "__main__":
    app = TeacherApp()
    app.mainloop()