import tkinter as tk
from tkinter import messagebox, ttk
from PIL import Image, ImageTk
import io
import os
import sys
import datetime

# Database import
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)
from utils.database import db_connect


class ClassroomFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#F0F4F8")
        self.controller = controller

        # User session
        self.username = None
        self.employee_id = None
        self.real_teacher_name = None

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
            fg="white"
        ).pack(side="right", padx=10, pady=25)

        self.active_label = tk.Label(
            header,
            text="Active: ---",
            font=("Helvetica", 10),
            bg="#0047AB",
            fg="#B0C4DE"
        )
        self.active_label.pack(side="right", padx=10)

        # ================= MAIN =================
        main_body = tk.Frame(self, bg="#F0F4F8")
        main_body.pack(fill="both", expand=True, padx=20, pady=10)

        left_col = tk.Frame(main_body, bg="#F0F4F8")
        left_col.pack(side="left", fill="both", expand=True)

        self.right_col = tk.Frame(main_body, bg="white", width=520)
        self.right_col.pack(side="right", fill="y")
        self.right_col.pack_propagate(False)

        self.setup_controls(left_col)
        self.setup_profile_panel()
        self.setup_table(left_col)

    # ================= USER LOADING =================
    def load_user(self, user_data):
        self.username = user_data.get("username")
        self.employee_id = user_data.get("employee_id")

        self.real_teacher_name = self.username
        self.active_label.config(text=f"Active: {self.username}")

        self.refresh_tables()

    # ================= CONTROLS =================
    def setup_controls(self, parent):
        panel = tk.Frame(parent, bg="white")
        panel.pack(fill="x", pady=10)

        tk.Label(panel, text="Student ID:", bg="white").grid(row=0, column=0)

        self.sid_var = tk.StringVar()
        self.sid_var.trace_add("write", self.verify_student)

        tk.Entry(panel, textvariable=self.sid_var).grid(row=0, column=1)

        self.name_var = tk.StringVar(value="Enter ID...")
        tk.Label(panel, textvariable=self.name_var, bg="white").grid(row=1, column=1)

        self.add_btn = tk.Button(panel, text="ADD", state="disabled",
                                 command=self.add_student)
        self.add_btn.grid(row=0, column=2, rowspan=2, padx=10)

        self.remove_btn = tk.Button(panel, text="REMOVE",
                                    command=self.remove_student)
        self.remove_btn.grid(row=0, column=3, rowspan=2)

    # ================= TABLE =================
    def setup_table(self, parent):
        cols = ("ID", "Student ID", "Name", "Guardian", "Contact")

        frame = tk.Frame(parent)
        frame.pack(fill="both", expand=True)

        self.tree = ttk.Treeview(frame, columns=cols, show="headings")

        for c in cols:
            self.tree.heading(c, text=c)
            self.tree.column(c, width=120)

        self.tree.pack(fill="both", expand=True)

    # ================= PROFILE =================
    def setup_profile_panel(self):
        tk.Label(self.right_col, text="PROFILE",
                 font=("Arial", 12, "bold"), bg="white").pack(pady=10)

        self.photo_label = tk.Label(self.right_col, text="No Image", bg="#ddd")
        self.photo_label.pack(pady=10)

        self.info_label = tk.Label(self.right_col, text="Select student",
                                   bg="white")
        self.info_label.pack()

    # ================= VERIFY =================
    def verify_student(self, *args):
        sid = self.sid_var.get().strip()

        if not sid:
            self.add_btn.config(state="disabled")
            self.name_var.set("Enter ID...")
            return

        try:
            with db_connect() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT Student_name FROM student WHERE Student_id=%s", (sid,))
                    res = cur.fetchone()

                    if res:
                        self.name_var.set(res[0])
                        self.add_btn.config(state="normal")
                    else:
                        self.name_var.set("NOT FOUND")
                        self.add_btn.config(state="disabled")
        except Exception as e:
            print(e)

    # ================= ADD =================
    def add_student(self):
        sid = self.sid_var.get().strip()

        try:
            with db_connect() as conn:
                with conn.cursor() as cur:

                    # prevent duplicate
                    cur.execute("SELECT id FROM classroom WHERE employee_id=%s AND student_id=%s",
                                (self.employee_id, sid))
                    if cur.fetchone():
                        messagebox.showwarning("Exists", "Already added")
                        return

                    cur.execute("INSERT INTO classroom (employee_id, student_id) VALUES (%s,%s)",
                                (self.employee_id, sid))
                    conn.commit()

            self.sid_var.set("")
            self.refresh_tables()

        except Exception as e:
            messagebox.showerror("Error", str(e))

    # ================= REMOVE =================
    def remove_student(self):
        sel = self.tree.focus()
        if not sel:
            return

        data = self.tree.item(sel, "values")
        sid = data[1]

        try:
            with db_connect() as conn:
                with conn.cursor() as cur:
                    cur.execute("DELETE FROM classroom WHERE student_id=%s AND employee_id=%s",
                                (sid, self.employee_id))
                    conn.commit()

            self.refresh_tables()

        except Exception as e:
            messagebox.showerror("Error", str(e))

    # ================= LOAD TABLE =================
    def refresh_tables(self):
        self.tree.delete(*self.tree.get_children())

        try:
            with db_connect() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT c.id, s.Student_id, s.Student_name,
                               s.Guardian_name, s.Guardian_contact
                        FROM classroom c
                        JOIN student s ON c.student_id=s.Student_id
                        WHERE c.employee_id=%s
                    """, (self.employee_id,))

                    for row in cur.fetchall():
                        self.tree.insert("", "end", values=row)

        except Exception as e:
            print("Refresh error:", e)

    # ================= SELECT =================
    def on_select(self, event):
        sel = self.tree.focus()
        if not sel:
            return

        data = self.tree.item(sel, "values")
        sid = data[1]

        self.load_profile(sid)

    # ================= PROFILE LOAD =================
    def load_profile(self, student_id):
        try:
            with db_connect() as conn:
                with conn.cursor(dictionary=True) as cur:

                    cur.execute("SELECT Student_name, grade_lvl, photo_path FROM student WHERE Student_id=%s",
                                (student_id,))
                    s = cur.fetchone()

                    if not s:
                        return

                    self.info_label.config(text=f"{s['Student_name']}\nGrade: {s['grade_lvl']}")

                    if s['photo_path']:
                        img = Image.open(io.BytesIO(s['photo_path']))
                        img.thumbnail((180, 180))
                        self.photo_img = ImageTk.PhotoImage(img)
                        self.photo_label.config(image=self.photo_img, text="")

        except Exception as e:
            print(e)
