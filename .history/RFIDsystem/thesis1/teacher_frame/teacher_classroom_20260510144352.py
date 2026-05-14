import tkinter as tk
from tkinter import messagebox, ttk
from PIL import Image, ImageTk
import io
import os, sys
from datetime import datetime

# Ensure utility imports work
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

        # FIX: prevent crash in check_for_updates
        self.last_log_id = None

        # ================= HEADER =================
        header = tk.Frame(self, bg="#0047AB", height=70)
        header.pack(fill="x")

        tk.Label(
            header,
            text="🍎 TEACHER DASHBOARD",
            font=("Helvetica", 18, "bold"),
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

        # ================= MAIN LAYOUT =================
        main_body = tk.Frame(self, bg="#F0F4F8")
        main_body.pack(fill="both", expand=True, padx=15, pady=10)

        left_col = tk.Frame(main_body, bg="#F0F4F8")
        left_col.pack(side="left", fill="both", expand=True)

        self.right_col = tk.Frame(
            main_body,
            bg="white",
            width=430,
            highlightthickness=1,
            highlightbackground="#D6DEE8"
        )
        self.right_col.pack(side="right", fill="y", padx=(15, 0))
        self.right_col.pack_propagate(False)

        # ================= TABLE =================
        self.setup_tables(left_col)
        self.setup_profile_panel()

        # start background checker
        self.check_for_updates()

    # ================= DB =================
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
            print(e)
            return self.username

    # ================= UI TABLE =================
    def setup_tables(self, parent):

        action_panel = tk.Frame(parent, bg="white")
        action_panel.pack(fill="x", pady=(0, 12), ipady=8)

        tk.Label(action_panel, text="STUDENT ID:", bg="white").grid(row=0, column=0)

        self.search_id_var = tk.StringVar()
        self.search_id_var.trace_add("write", self.verify_student_id)

        self.id_entry = tk.Entry(action_panel, textvariable=self.search_id_var)
        self.id_entry.grid(row=0, column=1)

        self.found_name_var = tk.StringVar(value="Enter Student ID")

        self.name_display = tk.Label(action_panel, textvariable=self.found_name_var, bg="white")
        self.name_display.grid(row=1, column=1)

        btn_frame = tk.Frame(action_panel, bg="white")
        btn_frame.grid(row=0, column=2, rowspan=2)

        self.add_btn = tk.Button(btn_frame, text="ADD TO CLASS",
                                  state="disabled",
                                  command=self.add_student_to_class)
        self.add_btn.pack()

        self.remove_btn = tk.Button(btn_frame, text="REMOVE",
                                    state="disabled",
                                    command=self.remove_student_from_class)
        self.remove_btn.pack()

        # TABLE
        cols = ("ID", "Student ID", "Full Name", "Guardian", "Contact")

        self.student_table = ttk.Treeview(parent, columns=cols, show="headings", height=15)

        for c in cols:
            self.student_table.heading(c, text=c)

        self.student_table.pack(fill="both", expand=True)

        self.student_table.bind("<<TreeviewSelect>>", self.on_student_select)

    # ================= PROFILE =================
    def setup_profile_panel(self):

        tk.Label(self.right_col, text="STUDENT PROFILE", bg="white",
                 font=("Arial", 11, "bold")).pack(pady=10)

        self.photo_label = tk.Label(self.right_col, text="No Image", bg="#E1E8EE")
        self.photo_label.pack(pady=10)

        self.info_label = tk.Label(self.right_col, text="Select student",
                                   bg="white", wraplength=350)
        self.info_label.pack(pady=10)

        self.history_table = ttk.Treeview(self.right_col,
                                           columns=("Time", "Fetcher", "Loc"),
                                           show="headings",
                                           height=8)

        for c in ("Time", "Fetcher", "Loc"):
            self.history_table.heading(c, text=c)

        self.history_table.pack(fill="both", expand=True)

    # ================= VERIFY =================
    def verify_student_id(self, *args):
        sid = self.search_id_var.get().strip()

        if not sid:
            self.found_name_var.set("Enter ID")
            self.add_btn.config(state="disabled")
            return

        try:
            with db_connect() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT Student_name FROM student WHERE Student_id=%s",
                        (sid,)
                    )
                    res = cur.fetchone()

                    if res:
                        self.found_name_var.set(res[0])
                        self.add_btn.config(state="normal")
                    else:
                        self.found_name_var.set("NOT FOUND")
                        self.add_btn.config(state="disabled")

        except Exception as e:
            print(e)

    # ================= ADD =================
    def add_student_to_class(self):
        sid = self.search_id_var.get()

        try:
            with db_connect() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "INSERT INTO classroom (teacher_name, student_id, employee_id) VALUES (%s,%s,%s)",
                        (self.real_teacher_name, sid, self.employee_id)
                    )
                    conn.commit()

            self.refresh_tables()

        except Exception as e:
            messagebox.showerror("Error", str(e))

    # ================= REMOVE =================
    def remove_student_from_class(self):
        sel = self.student_table.focus()
        if not sel:
            return

        data = self.student_table.item(sel, "values")
        sid = data[1]

        with db_connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM classroom WHERE student_id=%s AND teacher_name=%s",
                    (sid, self.real_teacher_name)
                )
                conn.commit()

        self.refresh_tables()

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
                        WHERE c.teacher_name=%s
                    """, (self.real_teacher_name,))

                    for row in cur.fetchall():
                        self.student_table.insert("", "end", values=row)

        except Exception as e:
            print(e)

    # ================= SELECT =================
    def on_student_select(self, event):
        sel = self.student_table.focus()
        if not sel:
            return

        data = self.student_table.item(sel, "values")
        self.load_full_student_details(data[1])

    # ================= DETAILS =================
    def load_full_student_details(self, student_id):

        with db_connect() as conn:
            with conn.cursor(dictionary=True) as cur:

                cur.execute("""
                    SELECT Student_name, grade_lvl, photo_path
                    FROM student WHERE Student_id=%s
                """, (student_id,))

                student = cur.fetchone()

                if not student:
                    return

                self.info_label.config(
                    text=f"{student['Student_name']}\nGrade: {student['grade_lvl']}"
                )

                if student["photo_path"]:
                    img = Image.open(io.BytesIO(student["photo_path"]))
                    img.thumbnail((180, 180))

                    self.current_photo = ImageTk.PhotoImage(img)
                    self.photo_label.config(image=self.current_photo, text="")
                else:
                    self.photo_label.config(text="No Photo")

    # ================= BACKGROUND CHECK =================
    def check_for_updates(self):
        try:
            with db_connect() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT student_name, time_out
                        FROM history_log
                        WHERE teacher=%s
                        ORDER BY time_out DESC LIMIT 1
                    """, (self.real_teacher_name,))

                    row = cur.fetchone()

                    if row:
                        name, t = row

                        if self.last_log_id != str(t):
                            if self.last_log_id is not None:
                                messagebox.showinfo("Fetched", f"{name} picked up")

                            self.last_log_id = str(t)

        except Exception as e:
            print(e)

        self.after(5000, self.check_for_updates)

    # ================= LOAD USER =================
    def load_user(self, user_data):
        self.username = user_data.get("username")
        self.employee_id = user_data.get("employee_id")

        self.real_teacher_name = self.get_teacher_display_name()