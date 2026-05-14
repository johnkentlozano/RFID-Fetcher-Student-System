import tkinter as tk
from tkinter import messagebox

# ================= IMPORT FRAMES =================
from teacher_frame.teacher_login import TeacherLoginFrame
from teacher_frame.teacher_signup import TeacherSignUpFrame
from teacher_frame.teacher_classroom import ClassroomFrame
from teacher_frame.forgot_pass_teacher import ForgotPasswordFrame
from teacher_frame.teacher_download_info import TeacherDownloadFrame
from teacher_frame.teacher_dashboard import TeacherDashboard


class TeacherApp(tk.Tk):
    def __init__(self):
        super().__init__()

        # ================= WINDOW SETTINGS =================
        self.title("Teacher System")
        self.geometry("1200x700")
        self.resizable(False, False)

        self.current_user = None

        # ================= MAIN CONTAINER =================
        container = tk.Frame(self)
        container.pack(fill="both", expand=True)

        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.frames = {}

        # ================= LOAD ALL FRAMES =================
        frame_classes = (
            TeacherLoginFrame,
            TeacherSignUpFrame,
            ForgotPasswordFrame,
            TeacherDashboard,
            ClassroomFrame,
            TeacherDownloadFrame,
        )

        for F in frame_classes:
            frame = F(container, self)
            self.frames[F.__name__] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        # ================= START FRAME =================
        self.show_frame("TeacherLoginFrame")

    # ================= SWITCH FRAME =================
    def show_frame(self, frame_name):
        frame = self.frames.get(frame_name)

        if frame:
            frame.tkraise()
        else:
            messagebox.showerror(
                "Frame Error",
                f"Frame '{frame_name}' not found."
            )

    # ================= LOGIN SUCCESS =================
    def login_success(self, user_data):

        # Check if Teacher
        if user_data.get("role") != "Teacher":
            messagebox.showerror(
                "Access Denied",
                "Teachers only!"
            )
            return

        self.current_user = user_data

        # Load teacher info to dashboard
        dashboard = self.frames["TeacherDashboard"]

        if hasattr(dashboard, "load_user"):
            dashboard.load_user(user_data)

        # Open dashboard
        self.show_frame("TeacherDashboard")

    # ================= LOGOUT =================
    def logout(self):
        self.current_user = None
        self.show_frame("TeacherLoginFrame")


# ================= RUN APP =================
if __name__ == "__main__":
    app = TeacherApp()
    app.mainloop()