import tkinter as tk
from tkinter import messagebox, ttk
from PIL import Image, ImageTk
import io
import os, sys
import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)
from utils.database import db_connect


class ClassroomFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#F0F4F8")
        self.controller = controller

        self.username = None
        self.employee_id = None
        self.real_teacher_name = None

        # IMPORTANT FIX (missing variable crash prevention)
        self.last_log_id = None

        self.check_for_updates()

        # ================= HEADER (UNCHANGED) =================
        header = tk.Frame(self, bg="#0047AB", height=80)
        header.pack(fill="x")

        tk.Label(
            header,
            text="🍎 TEACHER DASHBOARD",
            font=("Helvetica", 20, "bold"),
            bg="#0047AB",
            fg="white"
        ).pack(side="left", padx=20, pady=15)

        tk.Button(
            header,
            text="🔄 REFRESH",
            command=self.refresh_tables,
            bg="#2196F3",
            fg="white",
            bd=0,
            padx=10
        ).pack(side="right", padx=10, pady=25)

        tk.Label(
            header,
            text=f"Active: {self.real_teacher_name}",
            font=("Helvetica", 10),
            bg="#0047AB",
            fg="#B0C4DE"
        ).pack(side="right", padx=10)

        # ================= MAIN LAYOUT (UNCHANGED) =================
        main_body = tk.Frame(self, bg="#F0F4F8")
        main_body.pack(fill="both", expand=True, padx=20, pady=10)

        left_col = tk.Frame(main_body, bg="#F0F4F8")
        left_col.pack(side="left", fill="both", expand=True)

        self.right_col = tk.Frame(
            main_body,
            bg="white",
            width=520,
            highlightthickness=1,
            highlightbackground="#D1D9E6"
        )
        self.right_col.pack(side="right", fill="y", padx=(15, 0))
        self.right_col.pack_propagate(False)

        self.setup_profile_panel()
        self.setup_tables(left_col)

        self.student_table.bind("<<TreeviewSelect>>", self.on_student_select)
        self.refresh_tables()

    # ================= DATABASE FIX ONLY =================

    def get_teacher_display_name(self):
        try:
            if not self.username:
                return "Unknown Teacher"

            with db_connect() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT Teacher_name FROM teacher WHERE Teacher_name = %s",
                        (self.username,)
                    )
                    res = cur.fetchone()
                    return res[0] if res else self.username

        except Exception as e:
            messagebox.showwarning("Teacher name error", str(e))
            return self.username

    # ================= VERIFY (NO UI CHANGE) =================

    def verify_student_id(self, *args):
        sid = self.search_id_var.get().strip()
        if not sid:
            self.found_name_var.set("Enter ID...")
            self.add_btn.config(state="disabled")
            return

        try:
            with db_connect() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT Student_name FROM student WHERE Student_id = %s",
                        (sid,)
                    )
                    res = cur.fetchone()

                    if res:
                        self.found_name_var.set(res[0])
                        self.name_display.config(fg="green")
                        self.add_btn.config(state="normal")
                    else:
                        self.found_name_var.set("ID Not Found")
                        self.name_display.config(fg="red")
                        self.add_btn.config(state="disabled")

        except Exception as e:
            messagebox.showerror("Error", str(e))

    # ================= 🔥 FIXED INSERT (MAIN FIX) =================

    def add_student_to_class(self):
        sid = self.search_id_var.get().strip()

        if not messagebox.askyesno("Confirm", "Add student?"):
            return

        try:
            with db_connect() as conn:
                with conn.cursor() as cur:

                    # prevent duplicates (FIXED)
                    cur.execute("""
                        SELECT id FROM classroom 
                        WHERE employee_id = %s AND student_id = %s
                    """, (self.employee_id, sid))

                    if cur.fetchone():
                        messagebox.showwarning("Exists", "Student already in class")
                        return

                    # FIXED INSERT (NO teacher_name mismatch)
                    cur.execute("""
                        INSERT INTO classroom (employee_id, student_id)
                        VALUES (%s, %s)
                    """, (self.employee_id, sid))

                    conn.commit()

            self.search_id_var.set("")
            self.refresh_tables()

        except Exception as e:
            messagebox.showerror("Database Error", str(e))

    # ================= REMOVE FIX =================

    def remove_student_from_class(self):
        sel = self.student_table.focus()
        if not sel:
            return

        data = self.student_table.item(sel, "values")
        sid = data[1]

        try:
            with db_connect() as conn:
                with conn.cursor() as cur:
                    # FIXED DELETE
                    cur.execute("""
                        DELETE FROM classroom 
                        WHERE student_id = %s AND employee_id = %s
                    """, (sid, self.employee_id))

                    conn.commit()

            self.refresh_tables()

        except Exception as e:
            messagebox.showerror("Error", str(e))

    # ================= REFRESH FIX =================

    def refresh_tables(self):
        self.student_table.delete(*self.student_table.get_children())

        try:
            with db_connect() as conn:
                with conn.cursor() as cur:

                    # FIXED JOIN FILTER
                    cur.execute("""
                        SELECT 
                            c.id,
                            s.Student_id,
                            s.Student_name,
                            s.Guardian_name,
                            s.Guardian_contact
                        FROM classroom c
                        JOIN student s ON c.student_id = s.Student_id
                        WHERE c.employee_id = %s
                    """, (self.employee_id,))

                    for row in cur.fetchall():
                        self.student_table.insert("", "end", values=row)

        except Exception as e:
            print("Refresh Error:", e)

    # ================= PROFILE (UNCHANGED) =================
    def load_full_student_details(self, student_id):
        try:
            with db_connect() as conn:
                with conn.cursor(dictionary=True) as cur:

                    cur.execute("""
                        SELECT Student_name, grade_lvl, photo_path
                        FROM student
                        WHERE Student_id = %s
                    """, (student_id,))

                    student = cur.fetchone()
                    if not student:
                        return

                    self.info_label.config(
                        text=f"{student['Student_name']}\nGrade: {student['grade_lvl']}"
                    )

                    if student['photo_path']:
                        img = Image.open(io.BytesIO(student['photo_path']))
                        img.thumbnail((180, 180))
                        self.current_photo = ImageTk.PhotoImage(img)
                        self.photo_label.config(image=self.current_photo, text="")

        except Exception as e:
            messagebox.showerror("Error", str(e))

    # ================= FIXED LOG CHECK =================

    def check_for_updates(self):
        try:
            with db_connect() as conn:
                with conn.cursor() as cur:

                    cur.execute("""
                        SELECT student_name, time_out 
                        FROM history_log 
                        WHERE teacher = %s 
                        ORDER BY time_out DESC 
                        LIMIT 1
                    """, (self.real_teacher_name,))

                    new_log = cur.fetchone()

                    if new_log:
                        s_name, t_out = new_log

                        if self.last_log_id != str(t_out):
                            if self.last_log_id is not None:
                                self.notify_teacher(s_name, t_out)

                            self.last_log_id = str(t_out)

        except Exception as e:
            messagebox.showerror("Error", str(e))

        self.after(5000, self.check_for_updates)

    def notify_teacher(self, student_name, time_out):
        messagebox.showinfo(
            "Student Fetched",
            f"{student_name} picked up!\nTime: {time_out}"
        )

    # ================= USER LOAD =================

    def load_user(self, user_data):
        self.username = user_data.get("username")
        self.employee_id = user_data.get("employee_id")

        self.real_teacher_name = self.get_teacher_display_name()

        print("Loaded:", self.username)