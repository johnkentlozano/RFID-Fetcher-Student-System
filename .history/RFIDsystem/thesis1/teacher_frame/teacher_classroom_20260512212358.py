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
        self.last_log_id = None
        self.check_for_updates_started = False

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

        # ================= MAIN =================
        main_body = tk.Frame(self, bg="#F0F4F8")
        main_body.pack(fill="both", expand=True, padx=20, pady=10)

        left_col = tk.Frame(main_body, bg="#F0F4F8")
        left_col.pack(side="left", fill="both", expand=True)

        self.right_col = tk.Frame(main_body, bg="white", width=520)
        self.right_col.pack(side="right", fill="y")
        self.right_col.pack_propagate(False)

        self.setup_profile_panel()
        self.setup_tables(left_col)

        self.student_table.bind("<<TreeviewSelect>>", self.on_student_select)

    # ================= TEACHER NAME =================
    def get_teacher_display_name(self):
        try:
            with db_connect() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT employee_id FROM teacher WHERE employee_id = %s",
                        (self.employee_id,)
                    )
                    res = cur.fetchone()
                    return res[0] if res else self.employee_id
        except:
            return self.employee_id

    # ================= TABLE =================
    def setup_tables(self, parent):
        self.columns = ("ID", "Student ID", "Full Name", "Guardian", "Contact")
        self.student_table = ttk.Treeview(parent, columns=self.columns, show="headings")
        for c in self.columns:
            self.student_table.heading(c, text=c)
        self.student_table.pack(fill="both", expand=True)

    # ================= PROFILE =================
    def setup_profile_panel(self):
        self.info_label = tk.Label(self.right_col, text="Select a student...")
        self.info_label.pack()

        self.history_table = ttk.Treeview(
            self.right_col,
            columns=("Time", "Fetcher", "Loc"),
            show="headings"
        )
        self.history_table.pack(fill="both", expand=True)

    # ================= ADD =================
    def add_student_to_class(self):
        sid = self.search_id_var.get().strip()
        if not sid:
            return

        try:
            with db_connect() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT id FROM classroom
                        WHERE employee_id = %s AND student_id = %s
                    """, (self.employee_id, sid))

                    if cur.fetchone():
                        messagebox.showwarning("Exists", "Already added")
                        return

                    cur.execute("""
                        INSERT INTO classroom (employee_id, student_id)
                        VALUES (%s, %s)
                    """, (self.employee_id, sid))

                    conn.commit()

            self.refresh_tables()
            messagebox.showinfo("Success", "Added")

        except Exception as e:
            messagebox.showerror("Error", str(e))

    # ================= REMOVE =================
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
                        WHERE student_id = %s AND employee_id = %s
                    """, (sid, self.employee_id))
                    conn.commit()

            self.refresh_tables()

        except Exception as e:
            messagebox.showerror("Error", str(e))

    # ================= RESET =================
    def clear_entire_class(self):
        try:
            with db_connect() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        DELETE FROM classroom
                        WHERE employee_id = %s
                    """, (self.employee_id,))
                    conn.commit()

            self.refresh_tables()
            messagebox.showinfo("Success", "Class cleared")

        except Exception as e:
            messagebox.showerror("Error", str(e))

    # ================= REFRESH =================
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

                    for row in cur.fetchall():
                        self.student_table.insert("", "end", values=row)

        except Exception as e:
            print("Refresh Error:", e)

    # ================= HISTORY =================
    def check_for_updates(self):
        try:
            with db_connect() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT student_name, time_out
                        FROM history_log
                        WHERE employee_id = %s
                        ORDER BY time_out DESC
                        LIMIT 1
                    """, (self.employee_id,))

                    new_log = cur.fetchone()

                    if new_log:
                        s_name, t_out = new_log

                        if self.last_log_id != str(t_out):
                            if self.last_log_id:
                                self.notify_teacher(s_name, t_out)

                            self.last_log_id = str(t_out)

        except Exception as e:
            print("Update Error:", e)

        self.after(5000, self.check_for_updates)

    def notify_teacher(self, name, time):
        messagebox.showinfo("Fetched", f"{name} at {time}")

    # ================= SAVE LOG =================
    def save_fetch_log(self, student_data, auth_result):
        try:
            with db_connect() as conn:
                with conn.cursor() as cur:

                    now = datetime.datetime.now()

                    cur.execute("""
                        INSERT INTO history_log
                        (fetcher_name, student_name, student_id,
                         grade, employee_id, location, time_out)
                        VALUES (%s,%s,%s,%s,%s,%s,%s)
                    """, (
                        auth_result.get("name", "Fetcher"),
                        student_data['Student_name'],
                        student_data['Student_id'],
                        student_data.get('grade', ''),
                        self.employee_id,
                        "Classroom",
                        now
                    ))

                    conn.commit()

        except Exception as e:
            messagebox.showerror("Error", str(e))

    # ================= LOAD USER =================
    def load_user(self, user_data):
        self.username = user_data.get("username")
        self.employee_id = user_data.get("employee_id")
        self.department = user_data.get("department", "No Department")

        self.real_teacher_name = self.get_teacher_display_name()

        self.teacher_label.config(
            text=f"Active: {self.real_teacher_name} | {self.department}"
        )

        if not self.check_for_updates_started:
            self.check_for_updates_started = True
            self.after(1500, self.check_for_updates)

        self.refresh_tables()