import tkinter as tk
from tkinter import messagebox, ttk
from PIL import Image, ImageTk
import io
import os
import sys

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
        self.last_log_id = None
        self.check_for_updates_started = False
        self.current_photo = None

        # Treeview style
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", rowheight=28, font=("Segoe UI", 10),
                        background="white", fieldbackground="white")
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"),
                        background="#0047AB", foreground="white")
        style.map("Treeview",
                  background=[("selected", "#0047AB")],
                  foreground=[("selected", "white")])

        # ================= HEADER =================
        header = tk.Frame(self, bg="#0047AB", height=80)
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(
            header,
            text="🍎 CLASSROOM MANAGER",
            font=("Helvetica", 20, "bold"),
            bg="#0047AB", fg="white"
        ).pack(side="left", padx=20, pady=15)

        tk.Button(
            header,
            text="🔄 REFRESH",
            command=self.refresh_tables,
            bg="#2196F3", fg="white",
            font=("Arial", 9, "bold"),
            bd=0, padx=12, cursor="hand2"
        ).pack(side="right", padx=10, pady=25)

        self.teacher_label = tk.Label(
            header,
            text="Active: Waiting for Login...",
            font=("Helvetica", 10),
            bg="#0047AB", fg="#B0C4DE"
        )
        self.teacher_label.pack(side="right", padx=10)

        # ================= MAIN LAYOUT =================
        main_body = tk.Frame(self, bg="#F0F4F8")
        main_body.pack(fill="both", expand=True, padx=20, pady=10)

        left_col = tk.Frame(main_body, bg="#F0F4F8")
        left_col.pack(side="left", fill="both", expand=True)

        self.right_col = tk.Frame(
            main_body, bg="white", width=540,
            highlightthickness=1, highlightbackground="#D1D9E6"
        )
        self.right_col.pack(side="right", fill="y", padx=(15, 0))
        self.right_col.pack_propagate(False)

        self.setup_profile_panel()
        self.setup_tables(left_col)

        self.student_table.bind("<<TreeviewSelect>>", self.on_student_select)

    # ================= TEACHER NAME =================
    def get_teacher_display_name(self):
        if not self.employee_id:
            return "Unknown Teacher"
        try:
            with db_connect() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT username FROM users WHERE employee_id = %s", (self.employee_id,))
                    res = cur.fetchone()
                    return res[0] if res else (self.username or "Unknown Teacher")
        except Exception as e:
            print(f"Teacher name error: {e}")
            return self.username or "Unknown Teacher"

    # ================= ACTION PANEL + TABLE =================
    def setup_tables(self, parent):

        # ---- Enroll card ----
        action_panel = tk.Frame(parent, bg="white", highlightthickness=1, highlightbackground="#D1D9E6")
        action_panel.pack(fill="x", pady=(0, 12), ipady=10)

        tk.Label(action_panel, text="ENROLL STUDENT", font=("Arial", 10, "bold"),
                 bg="white", fg="#0047AB").grid(row=0, column=0, columnspan=2,
                                                padx=15, pady=(10, 6), sticky="w")

        tk.Label(action_panel, text="STUDENT ID:", font=("Arial", 9, "bold"),
                 bg="white", fg="#374151").grid(row=1, column=0, padx=15, pady=5, sticky="e")

        self.search_id_var = tk.StringVar()
        self.search_id_var.trace_add("write", self.verify_student_id)
        self.id_entry = tk.Entry(action_panel, textvariable=self.search_id_var,
                                 width=18, font=("Arial", 11), relief="solid", bd=1)
        self.id_entry.grid(row=1, column=1, padx=5, pady=5, sticky="w")

        tk.Label(action_panel, text="CONFIRM NAME:", font=("Arial", 9, "bold"),
                 bg="white", fg="#374151").grid(row=2, column=0, padx=15, pady=5, sticky="e")

        self.found_name_var = tk.StringVar(value="Enter ID above...")
        self.name_display = tk.Label(action_panel, textvariable=self.found_name_var,
                                     font=("Arial", 11, "italic"), bg="white", fg="#0047AB")
        self.name_display.grid(row=2, column=1, sticky="w", padx=5)

        # ---- Buttons ----
        btn_frame = tk.Frame(action_panel, bg="white")
        btn_frame.grid(row=1, column=2, rowspan=2, padx=20)

        self.add_btn = tk.Button(
            btn_frame, text="➕  ADD TO CLASS",
            bg="#4CAF50", fg="white", font=("Arial", 9, "bold"),
            width=18, state="disabled", bd=0, pady=5, cursor="hand2",
            command=self.add_student_to_class
        )
        self.add_btn.pack(pady=3)

        self.remove_btn = tk.Button(
            btn_frame, text="➖  REMOVE FROM CLASS",
            bg="#F44336", fg="white", font=("Arial", 9, "bold"),
            width=18, state="disabled", bd=0, pady=5, cursor="hand2",
            command=self.remove_student_from_class
        )
        self.remove_btn.pack(pady=3)

        self.reset_btn = tk.Button(
            btn_frame, text="🗑  RESET CLASS",
            bg="#607D8B", fg="white", font=("Arial", 9, "bold"),
            width=18, bd=0, pady=5, cursor="hand2",
            command=self.clear_entire_class
        )
        self.reset_btn.pack(pady=3)

        # ---- Student count label ----
        self.count_label = tk.Label(parent, text="My Enrolled Students  (0)",
                                    font=("Arial", 12, "bold"), bg="#F0F4F8", fg="#0047AB")
        self.count_label.pack(anchor="w", pady=(0, 4))

        # ---- Table ----
        self.columns = ("ID", "Student ID", "Full Name", "Guardian", "Contact")
        self.student_table = self.create_table(parent, self.columns)

    def create_table(self, parent, cols):
        frame = tk.Frame(parent, bg="white",
                         highlightthickness=1, highlightbackground="#D1D9E6")
        frame.pack(fill="both", expand=True, pady=(0, 15))

        tree = ttk.Treeview(frame, columns=cols, show="headings", height=12)
        tree.tag_configure("odd",  background="#F8FAFC")
        tree.tag_configure("even", background="white")

        for c in cols:
            tree.heading(c, text=c.upper())
            tree.column(c, width=100, anchor="center")
        tree.column("Full Name", width=200, anchor="w")

        tree.pack(side="left", fill="both", expand=True)
        sb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        return tree

    # ================= PROFILE PANEL =================
    def setup_profile_panel(self):
        tk.Label(self.right_col, text="STUDENT PROFILE",
                 font=("Arial", 11, "bold"), bg="white", fg="#0047AB").pack(pady=15)

        # Photo frame with border
        photo_frame = tk.Frame(self.right_col, bg="#E1E8EE",
                               highlightthickness=1, highlightbackground="#D1D9E6")
        photo_frame.pack(pady=(0, 10), padx=20)

        self.photo_label = tk.Label(photo_frame, text="No Image",
                                    bg="#E1E8EE", width=25, height=10,
                                    font=("Arial", 9), fg="#607D8B")
        self.photo_label.pack()

        # Info card
        info_card = tk.Frame(self.right_col, bg="#F8FAFC",
                             highlightthickness=1, highlightbackground="#D1D9E6")
        info_card.pack(fill="x", padx=15, pady=(0, 10))

        self.info_label = tk.Label(info_card, text="Select a student to view details.",
                                   bg="#F8FAFC", justify="left",
                                   font=("Arial", 10), wraplength=360, fg="#374151")
        self.info_label.pack(pady=12, padx=12, anchor="w")

        # Fetch logs
        tk.Label(self.right_col, text="📌 RECENT FETCH LOGS",
                 font=("Arial", 10, "bold"), bg="white", fg="#0047AB").pack(pady=(5, 4))

        history_frame = tk.Frame(self.right_col, bg="white")
        history_frame.pack(fill="both", expand=True, padx=5, pady=(0, 10))

        cols = ("Time", "Fetcher", "Location")
        self.history_table = ttk.Treeview(history_frame, columns=cols,
                                          show="headings", height=8)
        for c in cols:
            self.history_table.heading(c, text=c.upper())
        self.history_table.column("Time",     width=110, anchor="center")
        self.history_table.column("Fetcher",  width=120, anchor="center")
        self.history_table.column("Location", width=100, anchor="center")

        self.history_table.pack(side="left", fill="both", expand=True)
        h_scroll = ttk.Scrollbar(history_frame, orient="vertical",
                                  command=self.history_table.yview)
        self.history_table.configure(yscrollcommand=h_scroll.set)
        h_scroll.pack(side="right", fill="y")

    # ================= VERIFY ID =================
    def verify_student_id(self, *args):
        sid = self.search_id_var.get().strip()
        if not sid:
            self.found_name_var.set("Enter ID above...")
            self.add_btn.config(state="disabled")
            return
        try:
            with db_connect() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT Student_name FROM student WHERE Student_id = %s", (sid,))
                    res = cur.fetchone()
                    if res:
                        self.found_name_var.set(f"✔  {res[0]}")
                        self.name_display.config(fg="#16A34A")
                        self.add_btn.config(state="normal")
                    else:
                        self.found_name_var.set("✘  ID Not Found")
                        self.name_display.config(fg="#DC2626")
                        self.add_btn.config(state="disabled")
        except Exception as e:
            print(f"Verify Error: {e}")

    # ================= ADD STUDENT =================
    def add_student_to_class(self):
        sid = self.search_id_var.get().strip()
        if not sid or not self.employee_id:
            return
        try:
            with db_connect() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT id FROM classroom WHERE employee_id = %s AND student_id = %s",
                                (self.employee_id, sid))
                    if cur.fetchone():
                        messagebox.showwarning("Already Exists", "Student is already in your class.")
                        return
                    cur.execute("INSERT INTO classroom (employee_id, student_id) VALUES (%s, %s)",
                                (self.employee_id, sid))
                    conn.commit()
            self.search_id_var.set("")
            self.refresh_tables()
            messagebox.showinfo("Success", "Student added successfully.")
        except Exception as e:
            messagebox.showerror("Database Error", str(e))

    # ================= REMOVE STUDENT =================
    def remove_student_from_class(self):
        sel = self.student_table.focus()
        if not sel:
            return
        data = self.student_table.item(sel, "values")
        sid = data[1]
        if not messagebox.askyesno("Remove Student",
                                   f"Remove {data[2]} from your class?\nThis cannot be undone."):
            return
        try:
            with db_connect() as conn:
                with conn.cursor() as cur:
                    cur.execute("DELETE FROM classroom WHERE student_id = %s AND employee_id = %s",
                                (sid, self.employee_id))
                    conn.commit()
            self.refresh_tables()
            self.photo_label.config(image='', text="No Image")
            self.info_label.config(text="Select a student to view details.")
            self.history_table.delete(*self.history_table.get_children())
            self.remove_btn.config(state="disabled")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    # ================= REFRESH =================
    def refresh_tables(self):
        if not self.employee_id:
            return
        self.student_table.delete(*self.student_table.get_children())
        try:
            with db_connect() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT c.id, c.student_id, s.Student_name, s.Guardian_name, s.Guardian_contact
                        FROM classroom c JOIN student s ON c.student_id = s.Student_id
                        WHERE c.employee_id = %s
                        ORDER BY s.Student_name
                    """, (self.employee_id,))
                    rows = cur.fetchall()

            for i, row in enumerate(rows):
                tag = "odd" if i % 2 == 0 else "even"
                self.student_table.insert("", "end", values=row, tags=(tag,))

            count = len(rows)
            self.count_label.config(text=f"My Enrolled Students  ({count})")

        except Exception as e:
            print("Refresh Error:", e)

    # ================= SELECT STUDENT =================
    def on_student_select(self, event):
        sel = self.student_table.focus()
        if not sel:
            return
        data = self.student_table.item(sel, "values")
        self.remove_btn.config(state="normal")
        self.load_full_student_details(data[1])

    # ================= STUDENT DETAILS =================
    def load_full_student_details(self, student_id):
        if not student_id:
            return
        try:
            with db_connect() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT Student_name, grade_lvl, photo_path FROM student WHERE Student_id = %s",
                                (student_id,))
                    student = cur.fetchone()
                    if not student:
                        return

                    name, grade, photo_blob = student
                    self.info_label.config(
                        text=f"👤  Name:     {name}\n📚  Grade:    {grade}\n🪪  ID:         {student_id}"
                    )

                    if photo_blob:
                        try:
                            img = Image.open(io.BytesIO(photo_blob))
                            img.thumbnail((180, 180))
                            self.current_photo = ImageTk.PhotoImage(img)
                            self.photo_label.config(image=self.current_photo, text="")
                        except:
                            self.photo_label.config(image='', text="Image Error")
                    else:
                        self.photo_label.config(image='', text="No Photo")

                    self.history_table.delete(*self.history_table.get_children())
                    cur.execute("""
                        SELECT time_out, fetcher_name, location
                        FROM history_log
                        WHERE student_id = %s
                        ORDER BY time_out DESC LIMIT 10
                    """, (student_id,))
                    for i, log in enumerate(cur.fetchall()):
                        tag = "odd" if i % 2 == 0 else "even"
                        self.history_table.insert("", "end", values=log, tags=(tag,))
        except Exception as e:
            print(f"Detail Load Error: {e}")

    # ================= POLLING =================
    def check_for_updates(self):
        if not self.employee_id:
            self.after(5000, self.check_for_updates)
            return
        try:
            with db_connect() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT student_name, time_out FROM history_log
                        WHERE employee_id = %s
                        ORDER BY time_out DESC LIMIT 1
                    """, (self.employee_id,))
                    new_log = cur.fetchone()
                    if new_log:
                        s_name, t_out = new_log
                        if self.last_log_id != str(t_out):
                            if self.last_log_id is not None:
                                self.notify_teacher(s_name, t_out)
                            self.last_log_id = str(t_out)
                            self.refresh_tables()
        except Exception as e:
            print("Update Error:", e)
        self.after(5000, self.check_for_updates)

    def notify_teacher(self, student_name, time_out):
        messagebox.showinfo("Student Fetched", f"🔔  {student_name} was picked up!\n🕐  Time: {time_out}")

    # ================= RESET CLASS =================
    def clear_entire_class(self):
        if not messagebox.askyesno("Confirm Reset",
                                   "⚠️  Remove ALL students from your class?\n\nThis is usually done at the start of a new school year."):
            return
        try:
            with db_connect() as conn:
                with conn.cursor() as cur:
                    cur.execute("DELETE FROM classroom WHERE employee_id = %s", (self.employee_id,))
                    conn.commit()
            self.refresh_tables()
            self.photo_label.config(image='', text="No Image")
            self.info_label.config(text="Select a student to view details.")
            self.history_table.delete(*self.history_table.get_children())
            messagebox.showinfo("Success", "Classroom has been cleared.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    # ================= LOAD USER =================
    def load_user(self, user_data):
        if not user_data or not isinstance(user_data, dict):
            print("Error: Received empty or invalid user_data in load_user")
            return

        self.username    = user_data.get("username") or ""
        self.employee_id = user_data.get("employee_id") or None
        dep              = user_data.get("department") or "N/A"

        self.real_teacher_name = self.get_teacher_display_name() if self.employee_id else "Unknown Teacher"
        self.teacher_label.config(text=f"Active: {self.real_teacher_name}  |  {dep}")

        if not self.check_for_updates_started:
            self.check_for_updates_started = True
            self.check_for_updates()

        self.refresh_tables()