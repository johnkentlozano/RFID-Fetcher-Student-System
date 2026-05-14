import tkinter as tk
from tkinter import messagebox, ttk
from PIL import Image, ImageTk
import io
import os, sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from utils.database import db_connect


class ClassroomFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#F0F4F8")
        self.controller = controller

        # USER DATA
        self.username = None
        self.employee_id = None
        self.real_teacher_name = None
        self.department = None

        self.last_timestamp = None

        # UI
        self.build_ui()

    # ================= UI =================
    def build_ui(self):

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

        self.teacher_label = tk.Label(
            header,
            text="Active: Loading...",
            font=("Helvetica", 10),
            bg="#0047AB",
            fg="#B0C4DE"
        )
        self.teacher_label.pack(side="right", padx=10)

        main_body = tk.Frame(self, bg="#F0F4F8")
        main_body.pack(fill="both", expand=True, padx=20, pady=10)

        left_col = tk.Frame(main_body, bg="#F0F4F8")
        left_col.pack(side="left", fill="both", expand=True)

        self.right_col = tk.Frame(main_body, bg="white", width=520)
        self.right_col.pack(side="right", fill="y", padx=(15, 0))
        self.right_col.pack_propagate(False)

        self.setup_tables(left_col)
        self.setup_profile_panel()

        self.student_table.bind("<<TreeviewSelect>>", self.on_student_select)

    # ================= LOAD USER =================
    def load_user(self, user_data):
        self.username = user_data.get("username")
        self.employee_id = user_data.get("employee_id")

        # get teacher + department
        try:
            with db_connect() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT Teacher_name, department
                        FROM teacher
                        WHERE Teacher_name = %s
                    """, (self.username,))
                    res = cur.fetchone()

            if res:
                self.real_teacher_name = res[0]
                self.department = res[1]
            else:
                self.real_teacher_name = self.username
                self.department = "Unknown"

            self.teacher_label.config(
                text=f"Active: {self.real_teacher_name} | {self.department}"
            )

        except Exception as e:
            print("Teacher load error:", e)

        # START LIVE UPDATES SAFELY
        self.after(1500, self.check_for_updates)

    # ================= TABLE =================
    def setup_tables(self, parent):

        tk.Label(parent, text="My Enrolled Students",
                 font=("Arial", 12, "bold"),
                 bg="#F0F4F8",
                 fg="#0047AB").pack(anchor="w")

        cols = ("ID", "Student ID", "Full Name", "Guardian", "Contact", "Department")
        self.student_table = ttk.Treeview(parent, columns=cols, show="headings")

        for c in cols:
            self.student_table.heading(c, text=c.upper())
            self.student_table.column(c, width=120)

        self.student_table.pack(fill="both", expand=True, pady=10)

    # ================= PROFILE =================
    def setup_profile_panel(self):
        tk.Label(self.right_col, text="STUDENT PROFILE",
                 font=("Arial", 11, "bold"),
                 bg="white",
                 fg="#0047AB").pack(pady=10)

        self.info_label = tk.Label(self.right_col, text="Select student...",
                                   bg="white", justify="left")
        self.info_label.pack(pady=10)

        self.history_table = ttk.Treeview(self.right_col,
                                          columns=("Time", "Fetcher", "Loc"),
                                          show="headings")

        for c in ("Time", "Fetcher", "Loc"):
            self.history_table.heading(c, text=c)

        self.history_table.pack(fill="both", expand=True)

    # ================= REFRESH CLASSROOM =================
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
                            s.Guardian_contact,
                            %s
                        FROM classroom c
                        JOIN student s ON c.student_id = s.Student_id
                        WHERE c.employee_id = %s
                    """, (self.department, self.employee_id))

                    for row in cur.fetchall():
                        self.student_table.insert("", "end", values=row)

        except Exception as e:
            print("Refresh error:", e)

    # ================= LIVE RFID UPDATE =================
    def check_for_updates(self):
        try:
            if not self.employee_id:
                self.after(3000, self.check_for_updates)
                return

            with db_connect() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT student_name, time_out
                        FROM history_log
                        WHERE teacher = %s
                        ORDER BY time_out DESC
                        LIMIT 1
                    """, (self.real_teacher_name,))

                    row = cur.fetchone()

                    if row:
                        name, ts = row

                        if self.last_timestamp != ts:
                            self.last_timestamp = ts
                            self.notify_teacher(name, ts)
                            self.refresh_tables()

        except Exception as e:
            print("Live update error:", e)

        self.after(3000, self.check_for_updates)

    # ================= NOTIFY =================
    def notify_teacher(self, name, time):
        messagebox.showinfo("RFID ALERT", f"{name} was fetched\nTime: {time}")

    # ================= SELECT STUDENT =================
    def on_student_select(self, event):
        sel = self.student_table.focus()
        if not sel:
            return

        data = self.student_table.item(sel, "values")
        student_id = data[1]

        try:
            with db_connect() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT Student_name, grade_lvl
                        FROM student
                        WHERE Student_id = %s
                    """, (student_id,))
                    s = cur.fetchone()

            if s:
                self.info_label.config(text=f"{s[0]}\nGrade: {s[1]}")

        except Exception as e:
            print(e)