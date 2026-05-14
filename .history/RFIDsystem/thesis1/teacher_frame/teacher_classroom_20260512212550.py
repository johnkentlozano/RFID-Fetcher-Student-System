import tkinter as tk
from tkinter import messagebox, ttk
from PIL import Image, ImageTk
import io
import os,sys
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

        # Bind event
        self.student_table.bind("<<TreeviewSelect>>", self.on_student_select)
        self.refresh_tables()

    # ================= DATABASE =================

    def get_teacher_display_name(self):
        try:
            if not self.employee_id:
                return "Unknown Teacher"

            with db_connect() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT employee_id FROM teacher WHERE employee_id = %s",
                        (self.employee_id,)
                    )
                    res = cur.fetchone()
                    return res[0] if res else self.employee_id

        except Exception as e:
            messagebox.showwarning("Teacher name error", str(e))
            return self.employee_id or "Unknown Teacher"

    # ================= TABLE & UI SETUP =================

    def setup_tables(self, parent):
        action_panel = tk.Frame(
            parent,
            bg="white",
            highlightthickness=1,
            highlightbackground="#D1D9E6"
        )
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

        self.add_btn = tk.Button(btn_frame, text="ADD TO CLASS", bg="#4CAF50", fg="white",
                                 font=("Arial", 9, "bold"), width=16, state="disabled",
                                 command=self.add_student_to_class)
        self.add_btn.pack(pady=2)

        self.remove_btn = tk.Button(btn_frame, text="REMOVE FROM CLASS", bg="#F44336", fg="white",
                                    font=("Arial", 9, "bold"), width=16, state="disabled",
                                    command=self.remove_student_from_class)
        self.remove_btn.pack(pady=2)
        
        self.reset_btn = tk.Button(btn_frame, text="RESET CLASS (NEW YEAR)", bg="#607D8B", fg="white",
                                   font=("Arial", 9, "bold"), width=16,
                                   command=self.clear_entire_class)
        self.reset_btn.pack(pady=5)

        tk.Label(parent, text="My Enrolled Students", font=("Arial", 12, "bold"),
                 bg="#F0F4F8", fg="#0047AB").pack(anchor="w")

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
        tk.Label(self.right_col, text="STUDENT PROFILE", font=("Arial", 11, "bold"),
                 bg="white", fg="#0047AB").pack(pady=15)

        self.photo_label = tk.Label(self.right_col, text="No Image", bg="#E1E8EE",
                                    width=25, height=10, relief="solid", bd=1)
        self.photo_label.pack(pady=10, padx=20)

        self.info_label = tk.Label(self.right_col, text="Select a student...",
                                   bg="white", justify="left", font=("Arial", 10), wraplength=360)
        self.info_label.pack(pady=20, padx=15, fill="x")
        
        tk.Label(self.right_col, text="📌 RECENT FETCH LOGS", font=("Arial", 10, "bold"),
                 bg="white", fg="#0047AB").pack(pady=(10, 5))

        history_frame = tk.Frame(self.right_col, bg="white")
        history_frame.pack(fill="both", expand=True, padx=5, pady=5)

        cols = ("Time", "Fetcher", "Loc")
        self.history_table = ttk.Treeview(history_frame, columns=cols, show="headings", height=8)
        self.history_table.heading("Time", text="TIME")
        self.history_table.heading("Fetcher", text="BY")
        self.history_table.heading("Loc", text="LOC")
        self.history_table.pack(side="left", fill="both", expand=True)

        ttk.Scrollbar(history_frame, orient="vertical",
                      command=self.history_table.yview).pack(side="right", fill="y")

    # ================= FIXED FUNCTIONS =================

    def remove_student_from_class(self):
        sel = self.student_table.focus()
        if not sel: return
        data = self.student_table.item(sel, "values")
        sid = data[1]

        try:
            with db_connect() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "DELETE FROM classroom WHERE student_id=%s AND employee_id=%s",
                        (sid, self.employee_id)
                    )
                    conn.commit()
            self.refresh_tables()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def clear_entire_class(self):
        try:
            with db_connect() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "DELETE FROM classroom WHERE employee_id=%s",
                        (self.employee_id,)
                    )
                    conn.commit()
            self.refresh_tables()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def save_fetch_log(self, student_data, auth_result):
        try:
            with db_connect() as conn:
                with conn.cursor() as cur:
                    now = datetime.datetime.now()

                    cur.execute("""
                        INSERT INTO history_log 
                        (fetcher_name, student_name, student_id, grade, employee_id, location, time_out)
                        VALUES (%s,%s,%s,%s,%s,%s,%s)
                    """, (
                        auth_result.get("name", "Fetcher"),
                        student_data['Student_name'],
                        student_data['Student_id'],
                        student_data.get('grade', ''),
                        self.employee_id,
                        "Classroom Dashboard",
                        now
                    ))
                    conn.commit()
        except Exception as e:
            messagebox.showerror("Error", str(e))
            
    def clear_entire_class(self):
        # 1. First Warning
        if not messagebox.askyesno("Confirm Reset", "Are you sure you want to remove ALL students from your class for the new school year?"):
            return
            
        # 2. Final Warning (Safety First!)
        if not messagebox.askretrycancel("Final Warning", "This action cannot be undone. Proceed?"):
            return

        try:
            with db_connect() as conn:
                with conn.cursor() as cur:
                    # Deletes only the students linked to THIS teacher
                    cur.execute("DELETE FROM classroom WHERE teacher_name = %s", (self.real_teacher_name,))
                    conn.commit()
            
            self.refresh_tables()
            self.info_label.config(text="Classroom Cleared.")
            messagebox.showinfo("Success", "Classroom is now empty. You can begin adding new students.")
        except Exception as e:
            messagebox.showerror("Database Error", f"Could not reset class: {e}")
            
    def load_user(self, user_data):
        self.user_data = user_data
        self.username = user_data.get("username")
        self.employee_id = user_data.get("employee_id")

    # safe default (IMPORTANT)
        self.department = user_data.get("department", "No Department")

    # NOW it's safe to call this
        self.real_teacher_name = self.get_teacher_display_name()

    # update label safely
        self.teacher_label.config(
        text=f"Active: {self.real_teacher_name} | {self.department}"
        )

        if not self.check_for_updates_started:
            self.check_for_updates_started = True
            self.after(1500, self.check_for_updates)

        print("Loaded user:", self.username)