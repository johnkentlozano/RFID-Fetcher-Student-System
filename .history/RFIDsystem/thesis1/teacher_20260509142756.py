import tkinter as tk
from teacher_frame.teacher_login import TeacherLoginFrame
from teacher_frame.teacher_classroom import ClassroomFrame
from teacher_frame.teacher_signup import TeacherSignUpFrame
from teacher_frame.forgot_pass_teacher import ForgotPasswordFrame


class TeacherApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Teacher System")
        self.geometry("1200x700")

        container = tk.Frame(self)
        container.pack(fill="both", expand=True)

        self.frames = {}

        for F in (
            TeacherLoginFrame,
            TeacherSignUpFrame,
            ClassroomFrame,
            ForgotPasswordFrame
        ):
            frame = F(container, self)
            self.frames[F.__name__] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        # ✅ FIXED: correct frame name
        self.show_frame("TeacherLoginFrame")

    def show_frame(self, name):
        self.frames[name].tkraise()

    def login_success(self, user_data):
        if user_data["role"] != "Teacher":
            from tkinter import messagebox
            messagebox.showerror("Access Denied", "Teachers only")
            return

        self.show_frame("TeacherClassroom")


if __name__ == "__main__":
    app = TeacherApp()
    app.mainloop()