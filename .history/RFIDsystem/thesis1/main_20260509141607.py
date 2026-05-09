import tkinter as tk
from tkinter import messagebox

# Teacher Frames
from teacher_frame.teacher_login import TeacherLoginFrame
from teacher_frame.teacher_signup import TeacherSignUpFrame
from teacher_frame.forgot_pass_teacher import ForgotPassword_teacher
from teacher_frame.teacher_classroom import TeacherClassroom


class TeacherApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("TEACHER SYSTEM")
        self.geometry("1200x700")

        self.current_user = None
        self.current_frame_name = "TeacherLoginFrame"

        self.container = tk.Frame(self)
        self.container.pack(fill="both", expand=True)

        self.frames = {}

        # ✅ LOAD ALL TEACHER FRAMES
        for FrameClass in (
            TeacherLoginFrame,
            TeacherSignUpFrame,
            ForgotPassword_teacher,
            TeacherClassroom
        ):
            frame = FrameClass(self.container, self)
            self.frames[FrameClass.__name__] = frame
            frame.place(relwidth=1, relheight=1)

        self.show_frame("TeacherLoginFrame")

    # ---------------- NAVIGATION ----------------
    def show_frame(self, name):
        restricted_pages = ["TeacherClassroom"]

        # 🔒 Require login
        if name in restricted_pages and self.current_user is None:
            self.show_frame("TeacherLoginFrame")
            return

        self.current_frame_name = name
        self.frames[name].tkraise()

    # ---------------- LOGIN SUCCESS ----------------
    def login_success(self, user_data):
        # 🔒 TEACHER ONLY CHECK
        if user_data.get("role") != "Teacher":
            messagebox.showerror("Access Denied", "Teachers only")
            return

        self.current_user = user_data
        self.show_frame("TeacherClassroom")

    # ---------------- LOGOUT ----------------
    def logout(self):
        self.current_user = None
        self.show_frame("TeacherLoginFrame")

    # ---------------- CLOSE APP ----------------
    def on_closing(self):
        self.destroy()


if __name__ == "__main__":
    app = TeacherApp()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()