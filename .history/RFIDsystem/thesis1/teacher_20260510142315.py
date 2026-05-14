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

        self.frames = {}

        # ✅ INCLUDE DASHBOARD
        for F in (
            TeacherLoginFrame,
            TeacherSignUpFrame,
            ForgotPasswordFrame,
            TeacherDashboard   # 👈 ADD THIS
        ):
            frame = F(container, self)
            self.frames[F.__name__] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame("TeacherLoginFrame")

    # ================= SWITCH FRAME =================
    def show_frame(self, name):
        frame = self.frames[name]
        frame.tkraise()

    # ================= LOGIN SUCCESS =================
    def login_success(self, user_data):
        if user_data.get("role") != "Teacher":
            messagebox.showerror("Access Denied", "Teachers only")
            return

        self.current_user = user_data

        dashboard = self.frames["TeacherDashboard"]
        dashboard.load_user(user_data)   # ✅ VERY IMPORTANT

    self.show_frame("TeacherDashboard")

    # ================= LOGOUT =================
    def logout(self):
        self.current_user = None
        self.show_frame("TeacherLoginFrame")


if __name__ == "__main__":
    app = TeacherApp()
    app.mainloop()