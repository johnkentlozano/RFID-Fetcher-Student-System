import tkinter as tk
from teacher_frames.teacher_login import TeacherLogin
from teacher_frames.teacher_classroom import TeacherClassroom
from teacher_framessign_up ipmport 
from utils.helpers import get_image_path

class TeacherApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Teacher System")
        self.geometry("1200x700")

        container = tk.Frame(self)
        container.pack(fill="both", expand=True)

        self.frames = {}

        for F in (TeacherLogin, TeacherClassroom):
            frame = F(container, self)
            self.frames[F.__name__] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame("TeacherLogin")

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