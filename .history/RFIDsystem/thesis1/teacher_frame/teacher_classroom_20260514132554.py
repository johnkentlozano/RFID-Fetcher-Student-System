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
        self.selected_student_id = None

        # ================= HEADER =================
        header = tk.Frame(self, bg="#0047AB", height=80)
        header.pack(fill="x")

        tk.Label(header, text="🍎 TEACHER DASHBOARD",
                 font=("Helvetica", 20, "bold"),
                 bg="#0047AB", fg="white").pack(side="left", padx=20, pady=15)

        self.teacher_label = tk.Label(header, text="Active: Loading...",
                                      font=("Helvetica", 10),
                                      bg="#0047AB", fg="#B0C4DE")
        self.teacher_label.pack(side="right", padx=10)

        # ================= MAIN =================
        main_body = tk.Frame(self, bg="#F0F4F8")
        main_body.pack(fill="both", expand=True, padx=20, pady=10)

        left_col = tk.Frame(main_body, bg="#F0F4F8")
        left_col.pack(side="left", fill="both", expand=True)

        self.right_col = tk.Frame(main_body, bg="white", width=520)
        self.right_col.pack(side="right", fill="y", padx=(15, 0))
        self.right_col.pack_propagate(False)

        self.setup_profile_panel()
        self.setup_tables(left_col)

        self.student_table.bind("<<TreeviewSelect>>", self.on_student_select)

    # ================= LOAD USER =================
    def load_user(self, user_data):
        self.username = user_data.get("username")
        self.employee_id = user_data.get("employee_id")
        dept = user_data.get("department", "No Department")

        self.teacher_label.config(
            text=f"Active: {self.username} | {dept}"
        )

        # 🔥 AUTO LOAD
        self.refresh_tables()

    # ================= TABLE =================
    def setup_tables(self, parent):
        tk.Label(parent, text="My Enrolled Students",
                 font=("Arial", 12, "bold"),
                 bg="#F0F4F8", fg="#0047AB").pack(anchor="w")

        cols = ("ID", "Student ID", "Full Name", "Guardian", "Contact")

        frame = tk.Frame(parent)
        frame.pack(fill="both", expand=True)

        self.student_table = ttk.Treeview(frame, columns=cols, show="headings")

        for c in cols:
            self.student_table.heading(c, text=c)
            self.student_table.column(c, anchor="center", width=120)

        self.student_table.column("Full Name", width=200, anchor="w")

        self.student_table.pack(side="left", fill="both", expand=True)

        sb = ttk.Scrollbar(frame, orient="vertical",
                           command=self.student_table.yview)
        self.student_table.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")

    def refresh_tables(self):
        self.student_table.delete(*self.student_table.get_children())

        try:
            with db_connect() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT c.id, c.student_id, s.Student_name,
                               s.Guardian_name, s.Guardian_contact
                        FROM classroom c
                        JOIN student s ON c.student_id = s.Student_id
                        WHERE c.employee_id = %s
                    """, (self.employee_id,))

                    rows = cur.fetchall() or []

                    for row in rows:
                        # 🔥 FIX NoneType
                        clean_row = tuple(
                            "N/A" if r is None else r for r in row
                        )
                        self.student_table.insert("", "end", values=clean_row)

        except Exception as e:
            print("Refresh Error:", e)

    # ================= PROFILE PANEL =================
    def setup_profile_panel(self):
        tk.Label(self.right_col, text="STUDENT PROFILE",
                 font=("Arial", 11, "bold"),
                 bg="white", fg="#0047AB").pack(pady=15)

        self.info_label = tk.Label(self.right_col,
                                   text="Select a student...",
                                   bg="white",
                                   justify="left",
                                   font=("Arial", 10),
                                   wraplength=360)
        self.info_label.pack(pady=20, padx=15)

        # 🔥 REMOVE BUTTON (FIXED — NOT DUPLICATED)
        self.remove_btn = tk.Button(
            self.right_col,
            text="❌ REMOVE STUDENT",
            bg="#F44336",
            fg="white",
            state="disabled",
            command=self.remove_selected_student
        )
        self.remove_btn.pack(pady=10)

    # ================= CLICK =================
    def on_student_select(self, event):
        sel = self.student_table.focus()
        if not sel:
            return

        data = self.student_table.item(sel, "values")
        self.selected_student_id = data[1]

        self.load_student_info(self.selected_student_id)
        self.remove_btn.config(state="normal")

    # ================= LOAD INFO =================
    def load_student_info(self, student_id):
        try:
            with db_connect() as conn:
                with conn.cursor(dictionary=True) as cur:

                    cur.execute("""
                        SELECT Student_name, grade_lvl
                        FROM student
                        WHERE Student_id = %s
                    """, (student_id,))
                    student = cur.fetchone()

                    if not student:
                        return

                    # LAST FETCHER
                    cur.execute("""
                        SELECT fetcher_name
                        FROM history_log
                        WHERE student_id = %s
                        ORDER BY time_out DESC
                        LIMIT 1
                    """, (student_id,))
                    log = cur.fetchone()

                    fetcher = log["fetcher_name"] if log else "No Fetch Yet"

                    name = student["Student_name"] or "N/A"
                    grade = student["grade_lvl"] or "N/A"

                    self.info_label.config(
                        text=f"Name: {name}\nGrade: {grade}\nLast Fetcher: {fetcher}"
                    )

        except Exception as e:
            messagebox.showerror("Error", str(e))

    # ================= REMOVE =================
    def remove_selected_student(self):
        if not self.selected_student_id:
            return

        if not messagebox.askyesno("Confirm", "Remove this student?"):
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
            self.info_label.config(text="Student removed.")
            self.remove_btn.config(state="disabled")

        except Exception as e:
            messagebox.showerror("Error", str(e))