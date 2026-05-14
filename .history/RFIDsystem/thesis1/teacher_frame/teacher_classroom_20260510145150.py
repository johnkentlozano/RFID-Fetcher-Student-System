import tkinter as tk
from tkinter import messagebox, ttk
from PIL import Image, ImageTk
import io
import os, sys
import datetime

# ================= THEME =================
PRIMARY = "#1E3A8A"
ACCENT = "#3B82F6"
BG = "#F8FAFC"
CARD = "#FFFFFF"
TEXT = "#111827"

# Ensure utility imports work
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)
from utils.database import db_connect


class ClassroomFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=BG)
        self.controller = controller

        self.username = None
        self.employee_id = None
        self.real_teacher_name = None
        self.last_log_id = None

        # ================= HEADER =================
        header = tk.Frame(self, bg=PRIMARY, height=70)
        header.pack(fill="x")

        tk.Label(
            header,
            text="🍎 TEACHER DASHBOARD",
            font=("Segoe UI", 18, "bold"),
            bg=PRIMARY,
            fg="white"
        ).pack(side="left", padx=20)

        self.active_label = tk.Label(
            header,
            text="Active: ...",
            font=("Segoe UI", 10),
            bg=PRIMARY,
            fg="#CBD5F5"
        )
        self.active_label.pack(side="right", padx=10)

        tk.Button(
            header,
            text="LOGOUT",
            command=lambda: controller.show_frame("LoginFrame"),
            bg="#EF4444",
            fg="white",
            bd=0,
            padx=10,
            cursor="hand2"
        ).pack(side="right", padx=5)

        tk.Button(
            header,
            text="REFRESH",
            command=self.refresh_tables,
            bg=ACCENT,
            fg="white",
            bd=0,
            padx=10,
            cursor="hand2"
        ).pack(side="right", padx=5)

        # Clock
        self.time_label = tk.Label(header, bg=PRIMARY, fg="white")
        self.time_label.pack(side="right", padx=10)
        self.update_time()

        # Notification bar
        self.notification_label = tk.Label(
            self,
            text="",
            bg="#DCFCE7",
            fg="#166534",
            font=("Arial", 10, "bold")
        )
        self.notification_label.pack(fill="x")

        # ================= MAIN =================
        main_body = tk.Frame(self, bg=BG)
        main_body.pack(fill="both", expand=True, padx=20, pady=10)

        left_col = tk.Frame(main_body, bg=BG)
        left_col.pack(side="left", fill="both", expand=True)

        self.right_col = tk.Frame(main_body, bg=CARD, width=520)
        self.right_col.pack(side="right", fill="y", padx=(15, 0))
        self.right_col.pack_propagate(False)

        self.setup_profile_panel()
        self.setup_tables(left_col)

        self.student_table.bind("<<TreeviewSelect>>", self.on_student_select)

    # ================= UTIL =================
    def update_time(self):
        now = datetime.datetime.now().strftime("%H:%M:%S")
        self.time_label.config(text=now)
        self.after(1000, self.update_time)

    def create_card(self, parent):
        return tk.Frame(parent, bg=CARD, highlightthickness=1, highlightbackground="#E5E7EB")

    def styled_button(self, parent, text, color, command):
        return tk.Button(
            parent,
            text=text,
            command=command,
            bg=color,
            fg="white",
            relief="flat",
            font=("Segoe UI", 10, "bold"),
            padx=10,
            pady=5,
            cursor="hand2"
        )

    # ================= DATABASE =================
    def get_teacher_display_name(self):
        try:
            with db_connect() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT Teacher_name FROM teacher WHERE Teacher_name = %s",
                        (self.username,)
                    )
                    res = cur.fetchone()
                    return res[0] if res else self.username
        except:
            return self.username

    # ================= TABLE =================
    def setup_tables(self, parent):
        action_panel = self.create_card(parent)
        action_panel.pack(fill="x", pady=10, ipady=10)

        tk.Label(action_panel, text="STUDENT ID:", bg=CARD).grid(row=0, column=0, padx=10)

        self.search_id_var = tk.StringVar()
        self.search_id_var.trace_add("write", self.verify_student_id)

        self.id_entry = tk.Entry(action_panel, textvariable=self.search_id_var)
        self.id_entry.grid(row=0, column=1)

        tk.Label(action_panel, text="CONFIRM NAME:", bg=CARD).grid(row=1, column=0)

        self.found_name_var = tk.StringVar(value="Enter ID...")
        self.name_display = tk.Label(action_panel, textvariable=self.found_name_var, bg=CARD)
        self.name_display.grid(row=1, column=1)

        btn_frame = tk.Frame(action_panel, bg=CARD)
        btn_frame.grid(row=0, column=2, rowspan=2, padx=20)

        self.add_btn = self.styled_button(btn_frame, "ADD", "#22C55E", self.add_student_to_class)
        self.add_btn.pack(pady=2)

        self.remove_btn = self.styled_button(btn_frame, "REMOVE", "#EF4444", self.remove_student_from_class)
        self.remove_btn.pack(pady=2)
        self.remove_btn.config(state="disabled")

        self.reset_btn = self.styled_button(btn_frame, "RESET", "#64748B", self.clear_entire_class)
        self.reset_btn.pack(pady=5)

        tk.Label(parent, text="My Students", bg=BG, fg=PRIMARY).pack(anchor="w")

        cols = ("ID", "Student ID", "Full Name", "Guardian", "Contact")
        self.student_table = self.create_table(parent, cols)

    def create_table(self, parent, cols):
        frame = tk.Frame(parent)
        frame.pack(fill="both", expand=True)

        tree = ttk.Treeview(frame, columns=cols, show="headings")
        for c in cols:
            tree.heading(c, text=c)
            tree.column(c, anchor="center")

        tree.pack(fill="both", expand=True)
        return tree

    # ================= PROFILE =================
    def setup_profile_panel(self):
        tk.Label(self.right_col, text="STUDENT PROFILE", bg=CARD, fg=PRIMARY).pack(pady=10)

        self.photo_label = tk.Label(self.right_col, bg="#E5E7EB", width=180, height=180)
        self.photo_label.pack(pady=10)

        self.info_label = tk.Label(self.right_col, text="Select student", bg=CARD)
        self.info_label.pack()

        self.history_table = ttk.Treeview(self.right_col, columns=("Time", "By", "Loc"), show="headings")
        self.history_table.pack(fill="both", expand=True)

    # ================= LOGIC =================
    def verify_student_id(self, *args):
        sid = self.search_id_var.get().strip()
        if not sid:
            return

        try:
            with db_connect() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT Student_name FROM student WHERE Student_id = %s", (sid,))
                    res = cur.fetchone()
                    if res:
                        self.found_name_var.set(res[0])
                        self.add_btn.config(state="normal")
        except:
            pass

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
            self.id_entry.focus()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def remove_student_from_class(self):
        sel = self.student_table.focus()
        if not sel:
            return

        data = self.student_table.item(sel, "values")

        try:
            with db_connect() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "DELETE FROM classroom WHERE student_id=%s AND teacher_name=%s",
                        (data[1], self.real_teacher_name)
                    )
                    conn.commit()

            self.refresh_tables()
        except Exception as e:
            messagebox.showerror("Error", str(e))

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
                        WHERE c.teacher_name = %s
                    """, (self.real_teacher_name,))

                    for row in cur.fetchall():
                        self.student_table.insert("", "end", values=row)
        except:
            pass

    def on_student_select(self, event):
        self.remove_btn.config(state="normal")

    def notify_teacher(self, student_name, time_out):
        self.notification_label.config(text=f"{student_name} picked up at {time_out}")

    def clear_entire_class(self):
        if not messagebox.askyesno("Confirm", "Reset class?"):
            return

        try:
            with db_connect() as conn:
                with conn.cursor() as cur:
                    cur.execute("DELETE FROM classroom WHERE teacher_name=%s", (self.real_teacher_name,))
                    conn.commit()

            self.refresh_tables()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    # ================= USER =================
    def load_user(self, user_data):
        self.user_data = user_data
        self.username = user_data.get("username")
        self.employee_id = user_data.get("employee_id")

        self.real_teacher_name = self.get_teacher_display_name()

        self.active_label.config(text=f"Active: {self.real_teacher_name}")

        messagebox.showinfo("Welcome", f"Logged in as {self.real_teacher_name}")

        self.refresh_tables()
        self.check_for_updates()

    # ================= BACKGROUND =================
    def check_for_updates(self):
        if not self.real_teacher_name:
            self.after(5000, self.check_for_updates)
            return

        try:
            with db_connect() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT student_name, time_out
                        FROM history_log
                        WHERE teacher=%s
                        ORDER BY time_out DESC LIMIT 1
                    """, (self.real_teacher_name,))
                    new_log = cur.fetchone()

                    if new_log:
                        name, time = new_log
                        if self.last_log_id != str(time):
                            if self.last_log_id:
                                self.notify_teacher(name, time)
                            self.last_log_id = str(time)

        except:
            pass

        self.after(5000, self.check_for_updates)