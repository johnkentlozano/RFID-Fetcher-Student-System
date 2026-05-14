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
        self.department = None

        self.last_log_id = None  # FIX: missing variable caused crash

        # ❌ FIX: DO NOT start updates here (teacher not loaded yet)
        # self.check_for_updates()

        self.check_for_updates_started = False  # FIX safety flag

        # ================= HEADER =================
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

        # ================= MAIN LAYOUT =================
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

    # ================= LOAD USER (FIXED ORDER) =================
    def load_user(self, user_data):
        self.user_data = user_data
        self.username = user_data.get("username")
        self.employee_id = user_data.get("employee_id")

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
            messagebox.showwarning("Teacher Error", str(e))

        # ✅ FIX: start updates ONLY after everything is ready
        if not self.check_for_updates_started:
            self.check_for_updates_started = True
            self.after(1500, self.check_for_updates)

    # ================= TABLE REFRESH =================
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

                    for row in cur.fetchall():
                        self.student_table.insert("", "end", values=row)

        except Exception as e:
            print("Refresh Error:", e)

    # ================= LIVE RFID UPDATE (FIXED) =================
    def check_for_updates(self):
        try:
            if not self.real_teacher_name:
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

                        if self.last_log_id != str(ts):
                            self.last_log_id = str(ts)
                            self.notify_teacher(name, ts)
                            self.refresh_tables()

        except Exception as e:
            print("Background Update Error:", e)

        self.after(3000, self.check_for_updates)

    # ================= DELETE FIX =================
    def remove_student_from_class(self):
        sel = self.student_table.focus()
        if not sel:
            return

        data = self.student_table.item(sel, "values")
        sid = data[1]

        try:
            with db_connect() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        DELETE FROM classroom 
                        WHERE student_id = %s 
                        AND employee_id = %s
                    """, (sid, self.employee_id))  # FIXED

                    conn.commit()

            self.refresh_tables()

        except Exception as e:
            messagebox.showerror("Error", str(e))

    # ================= RESET FIX =================
    def clear_entire_class(self):
        try:
            with db_connect() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        DELETE FROM classroom 
                        WHERE employee_id = %s
                    """, (self.employee_id,))  # FIXED

                    conn.commit()

            self.refresh_tables()

        except Exception as e:
            messagebox.showerror("Error", str(e))

    # ================= PROFILE =================
    def setup_profile_panel(self):
        self.photo_label = tk.Label(self.right_col, text="No Image")
        self.photo_label.pack()

        self.info_label = tk.Label(self.right_col, text="Select student...")
        self.info_label.pack()

        self.history_table = ttk.Treeview(
            self.right_col,
            columns=("Time", "Fetcher", "Loc"),
            show="headings"
        )
        self.history_table.pack(fill="both", expand=True)

    # ================= TABLE =================
    def setup_tables(self, parent):
        self.student_table = ttk.Treeview(
            parent,
            columns=("ID", "Student ID", "Full Name", "Guardian", "Contact"),
            show="headings"
        )

        self.student_table.pack(fill="both", expand=True)

    # ================= NOTIFY =================
    def notify_teacher(self, name, time):
        messagebox.showinfo("RFID ALERT", f"{name} fetched\n{time}")