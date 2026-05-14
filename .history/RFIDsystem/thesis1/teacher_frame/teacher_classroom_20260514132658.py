import tkinter as tk
from tkinter import messagebox, ttk
from PIL import Image, ImageTk
import io
import os,sys
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
        self.last_log_id = None
        self.check_for_updates_started = False
        self.selected_student_id = None

        # ================= HEADER =================
        header = tk.Frame(self, bg="#0047AB", height=80)
        header.pack(fill="x")

        tk.Label(header, text="🍎 TEACHER DASHBOARD",
                 font=("Helvetica", 20, "bold"),
                 bg="#0047AB", fg="white").pack(side="left", padx=20, pady=15)
        
        tk.Button(header, text="🔄 REFRESH",
                  command=self.refresh_tables,
                  bg="#2196F3", fg="white", bd=0, padx=10
                  ).pack(side="right", padx=10, pady=25)

        self.teacher_label = tk.Label(header, text="Active: Loading...",
                                     font=("Helvetica", 10),
                                     bg="#0047AB", fg="#B0C4DE")
        self.teacher_label.pack(side="right", padx=10)

        # ================= MAIN =================
        main_body = tk.Frame(self, bg="#F0F4F8")
        main_body.pack(fill="both", expand=True, padx=20, pady=10)

        left_col = tk.Frame(main_body, bg="#F0F4F8")
        left_col.pack(side="left", fill="both", expand=True)

        self.right_col = tk.Frame(main_body, bg="white", width=520,
                                 highlightthickness=1,
                                 highlightbackground="#D1D9E6")
        self.right_col.pack(side="right", fill="y", padx=(15, 0))
        self.right_col.pack_propagate(False)
        
        self.setup_profile_panel()
        self.setup_tables(left_col)

        self.student_table.bind("<<TreeviewSelect>>", self.on_student_select)

    # ================= LOAD USER =================
    def load_user(self, user_data):
        self.user_data = user_data
        self.username = user_data.get("username")
        self.employee_id = user_data.get("employee_id")
        self.department = user_data.get("department", "No Department")

        self.teacher_label.config(
            text=f"Active: {self.username} | {self.department}"
        )

        # ✅ AUTO LOAD ON LOGIN
        self.refresh_tables()

    # ================= TABLE =================
    def refresh_tables(self):
        self.student_table.delete(*self.student_table.get_children())

        try:
            with db_connect() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT 
                            c.id,
                            c.student_id,
                            s.Student_name,
                            s.Guardian_name,
                            s.Guardian_contact
                        FROM classroom c
                        JOIN student s ON c.student_id = s.Student_id
                        WHERE c.employee_id = %s
                    """, (self.employee_id,))

                    rows = cur.fetchall() or []

                    for row in rows:
                        clean = tuple("N/A" if r is None else r for r in row)
                        self.student_table.insert("", "end", values=clean)

        except Exception as e:
            print("Refresh Error:", e)

    # ================= CLICK =================
    def on_student_select(self, event):
        sel = self.student_table.focus()
        if not sel:
            return

        data = self.student_table.item(sel, "values")
        self.selected_student_id = data[1]

        self.remove_btn.config(state="normal")
        self.load_full_student_details(self.selected_student_id)

    # ================= PROFILE =================
    def load_full_student_details(self, student_id):
        try:
            with db_connect() as conn:
                with conn.cursor(dictionary=True) as cur:

                    # STUDENT INFO
                    cur.execute("""
                        SELECT Student_name, grade_lvl, photo_path
                        FROM student
                        WHERE Student_id = %s
                    """, (student_id,))
                    student = cur.fetchone()

                    if not student:
                        return

                    # LAST FETCHER
                    cur.execute("""
                        SELECT fetcher_name, time_out
                        FROM history_log
                        WHERE student_id = %s
                        ORDER BY time_out DESC
                        LIMIT 1
                    """, (student_id,))
                    log = cur.fetchone()

                    fetcher = log["fetcher_name"] if log else "No Fetch Yet"

                    # TEXT UPDATE
                    self.info_label.config(
                        text=f"{student['Student_name'] or 'N/A'}\n"
                             f"Grade: {student['grade_lvl'] or 'N/A'}\n"
                             f"Last Fetcher: {fetcher}"
                    )

                    # PHOTO
                    if student["photo_path"]:
                        stream = io.BytesIO(student["photo_path"])
                        img = Image.open(stream)
                        img.thumbnail((180, 180))
                        self.current_photo = ImageTk.PhotoImage(img)

                        self.photo_label.config(image=self.current_photo, text="")
                    else:
                        self.photo_label.config(image='', text="No Photo")

                    # HISTORY
                    self.history_table.delete(*self.history_table.get_children())

                    cur.execute("""
                        SELECT time_out, fetcher_name, location
                        FROM history_log
                        WHERE student_id = %s
                        ORDER BY time_out DESC
                        LIMIT 10
                    """, (student_id,))

                    for log in cur.fetchall():
                        self.history_table.insert("", "end", values=(
                            log["time_out"],
                            log["fetcher_name"],
                            log["location"]
                        ))

        except Exception as e:
            messagebox.showerror("Error", str(e))

    # ================= REMOVE =================
    def remove_student_from_class(self):
        if not self.selected_student_id:
            return

        if not messagebox.askyesno("Remove", "Remove this student?"):
            return

        try:
            with db_connect() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        DELETE FROM classroom 
                        WHERE student_id = %s AND employee_id = %s
                    """, (self.selected_student_id, self.employee_id))
                    conn.commit()

            self.refresh_tables()
            self.info_label.config(text="Select a student...")
            self.photo_label.config(image='', text="No Image")
            self.remove_btn.config(state="disabled")

        except Exception as e:
            messagebox.showerror("Error", str(e))