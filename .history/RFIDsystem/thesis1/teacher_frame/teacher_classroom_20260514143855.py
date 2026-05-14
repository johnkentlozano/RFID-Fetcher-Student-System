import tkinter as tk
from tkinter import messagebox, ttk
from PIL import Image, ImageTk
import io
import os
import sys
import datetime

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
            text="Active: Waiting for Login...",
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

    def get_teacher_display_name(self):
        if not self.employee_id:
            return "Unknown Teacher"
        try:
            with db_connect() as conn:
                with conn.cursor() as cur:
                    # Using users table to get the consistent display name
                    cur.execute("SELECT username FROM users WHERE employee_id = %s", (self.employee_id,))
                    res = cur.fetchone()
                    return res[0] if res else self.username
        except Exception as e:
            print(f"Teacher name error: {e}")
            return self.username

    def setup_tables(self, parent):
        action_panel = tk.Frame(parent, bg="white", highlightthickness=1, highlightbackground="#D1D9E6")
        action_panel.pack(fill="x", pady=(0, 15), ipady=10)

        tk.Label(action_panel, text="STUDENT ID:", font=("Arial", 10, "bold"), bg="white").grid(row=0, column=0, padx=10, pady=5, sticky="e")
        
        self.search_id_var = tk.StringVar()
        self.search_id_var.trace_add("write", self.verify_student_id)
        self.id_entry = tk.Entry(action_panel, textvariable=self.search_id_var, width=15, font=("Arial", 11))
        self.id_entry.grid(row=0, column=1, padx=5, sticky="w")

        tk.Label(action_panel, text="CONFIRM NAME:", font=("Arial", 10, "bold"), bg="white").grid(row=1, column=0, padx=10, pady=5, sticky="e")
        
        self.found_name_var = tk.StringVar(value="Enter ID...")
        self.name_display = tk.Label(action_panel, textvariable=self.found_name_var, font=("Arial", 11, "italic"), bg="white", fg="#0047AB")
        self.name_display.grid(row=1, column=1, sticky="w")

        btn_frame = tk.Frame(action_panel, bg="white")
        btn_frame.grid(row=0, column=2, rowspan=2, padx=20)

        self.add_btn = tk.Button(btn_frame, text="ADD TO CLASS", bg="#4CAF50", fg="white", font=("Arial", 9, "bold"), width=16, state="disabled", command=self.add_student_to_class)
        self.add_btn.pack(pady=2)

        self.remove_btn = tk.Button(btn_frame, text="REMOVE FROM CLASS", bg="#F44336", fg="white", font=("Arial", 9, "bold"), width=16, state="disabled", command=self.remove_student_from_class)
        self.remove_btn.pack(pady=2)
        
        self.reset_btn = tk.Button(btn_frame, text="RESET CLASS", bg="#607D8B", fg="white", font=("Arial", 9, "bold"), width=16, command=self.clear_entire_class)
        self.reset_btn.pack(pady=5)

        tk.Label(parent, text="My Enrolled Students", font=("Arial", 12, "bold"), bg="#F0F4F8", fg="#0047AB").pack(anchor="w")

        self.columns = ("ID", "Student ID", "Full Name", "Guardian", "Contact")
        self.student_table = self.create_table(parent, self.columns)

    def create_table(self, parent, cols):
        frame = tk.Frame(parent)
        frame.pack(fill="both", expand=True, pady=(5, 15))
        tree = ttk.Treeview(frame, columns=cols, show="headings", height=12)
        for c in cols:
            tree.heading(c, text=c.upper())
            tree.column(c, width=100, anchor="center")
        tree.column("Full Name", width=200, anchor="w")
        tree.pack(side="left", fill="both", expand=True)
        sb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        return tree

    def setup_profile_panel(self):
        tk.Label(self.right_col, text="STUDENT PROFILE", font=("Arial", 11, "bold"), bg="white", fg="#0047AB").pack(pady=15)
        self.photo_label = tk.Label(self.right_col, text="No Image", bg="#E1E8EE", width=25, height=10, relief="solid", bd=1)
        self.photo_label.pack(pady=10, padx=20)
        self.info_label = tk.Label(self.right_col, text="Select a student...", bg="white", justify="left", font=("Arial", 10), wraplength=360)
        self.info_label.pack(pady=20, padx=15, fill="x")
        
        tk.Label(self.right_col, text="📌 RECENT FETCH LOGS", font=("Arial", 10, "bold"), bg="white", fg="#0047AB").pack(pady=(10, 5))
        history_frame = tk.Frame(self.right_col, bg="white")
        history_frame.pack(fill="both", expand=True, padx=5, pady=5)

        cols = ("Time", "Fetcher", "Loc")
        self.history_table = ttk.Treeview(history_frame, columns=cols, show="headings", height=8)
        for c in cols: self.history_table.heading(c, text=c)
        self.history_table.column("Time", width=100, anchor="center")
        self.history_table.pack(side="left", fill="both", expand=True)
        h_scroll = ttk.Scrollbar(history_frame, orient="vertical", command=self.history_table.yview)
        self.history_table.configure(yscrollcommand=h_scroll.set)
        h_scroll.pack(side="right", fill="y")

    def verify_student_id(self, *args):
        sid = self.search_id_var.get().strip()
        if not sid:
            self.found_name_var.set("Enter ID...")
            self.add_btn.config(state="disabled")
            return
        try:
            with db_connect() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT Student_name FROM student WHERE Student_id = %s", (sid,))
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
            print(f"Verify Error: {e}")

    def add_student_to_class(self):
        sid = self.search_id_var.get().strip()
        if not sid or not self.employee_id: return
        try:
            with db_connect() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT id FROM classroom WHERE employee_id = %s AND student_id = %s", (self.employee_id, sid))
                    if cur.fetchone():
                        messagebox.showwarning("Already Exists", "Student already in your class.")
                        return
                    cur.execute("INSERT INTO classroom (employee_id, student_id) VALUES (%s, %s)", (self.employee_id, sid))
                    conn.commit()
            self.search_id_var.set("")
            self.refresh_tables()
            messagebox.showinfo("Success", "Student added successfully.")
        except Exception as e:
            messagebox.showerror("Database Error", str(e))

    def remove_student_from_class(self):
        sel = self.student_table.focus()
        if not sel: return
        data = self.student_table.item(sel, "values")
        sid = data[1]
        if not messagebox.askyesno("Remove", f"Remove {data[2]} from your class?"): return
        try:
            with db_connect() as conn:
                with conn.cursor() as cur:
                    cur.execute("DELETE FROM classroom WHERE student_id = %s AND employee_id = %s", (sid, self.employee_id))
                    conn.commit()
            self.refresh_tables()
            self.photo_label.config(image='', text="No Image")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def refresh_tables(self):
        if not self.employee_id: return
        self.student_table.delete(*self.student_table.get_children())
        try:
            with db_connect() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT c.id, c.student_id, s.Student_name, s.Guardian_name, s.Guardian_contact
                        FROM classroom c JOIN student s ON c.student_id = s.Student_id
                        WHERE c.employee_id = %s
                    """, (self.employee_id,))
                    for row in cur.fetchall():
                        self.student_table.insert("", "end", values=row)
        except Exception as e:
            print("Refresh Error:", e)

    def on_student_select(self, event):
        sel = self.student_table.focus()
        if not sel: return
        data = self.student_table.item(sel, "values")
        self.remove_btn.config(state="normal")
        self.load_full_student_details(data[1])

    def load_full_student_details(self, student_id):
        try:
            with db_connect() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT Student_name, grade_lvl, photo_path FROM student WHERE Student_id = %s", (student_id,))
                    student = cur.fetchone()
                    if not student: return

                    name, grade, photo_blob = student
                    self.info_label.config(text=f"Name: {name}\nGrade: {grade}")

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
                    cur.execute("SELECT time_out, fetcher_name, location FROM history_log WHERE student_id = %s ORDER BY time_out DESC LIMIT 10", (student_id,))
                    for log in cur.fetchall():
                        self.history_table.insert("", "end", values=log)
        except Exception as e:
            print(f"Detail Load Error: {e}")

    def check_for_updates(self):
        if not self.employee_id: 
            self.after(5000, self.check_for_updates)
            return
        try:
            with db_connect() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT student_name, time_out FROM history_log WHERE employee_id = %s ORDER BY time_out DESC LIMIT 1", (self.employee_id,))
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
        messagebox.showinfo("Student Fetched", f"🔔 {student_name} picked up!\nTime: {time_out}")

    def clear_entire_class(self):
        if not messagebox.askyesno("Confirm Reset", "Remove ALL students for the new year?"): return
        try:
            with db_connect() as conn:
                with conn.cursor() as cur:
                    cur.execute("DELETE FROM classroom WHERE employee_id = %s", (self.employee_id,))
                    conn.commit()
            self.refresh_tables()
            messagebox.showinfo("Success", "Classroom cleared.")
        except Exception as e:
            messagebox.showerror("Error", str(e))
            
    def load_user(self, user_data):
        # FIX for 'NoneType' object has no attribute 'get'
        if not user_data:
            print("Error: Received empty user_data in load_user")
            return

        self.username = user_data.get("username")
        self.employee_id = user_data.get("employee_id")
        dep = user_data.get("department", "N/A")
        self.real_teacher_name = self.get_teacher_display_name()

        self.teacher_label.config(text=f"Active: {self.real_teacher_name} | {dep}")
        
        if not self.check_for_updates_started:
            self.check_for_updates_started = True
            self.check_for_updates()
        
        self.refresh_tables()