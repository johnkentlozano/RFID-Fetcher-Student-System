import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
import csv

from utils.database import db_connect


class TeacherDownloadFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#F3F6FA")

        self.controller = controller

        # ================= STYLE =================
        style = ttk.Style()
        style.theme_use("default")

        style.configure("Treeview",
                        rowheight=28,
                        font=("Segoe UI", 10))

        style.configure("Treeview.Heading",
                        font=("Segoe UI", 10, "bold"))

        # ================= TITLE =================
        tk.Label(
            self,
            text="📥 Download Student Logs",
            font=("Segoe UI", 22, "bold"),
            bg="#F3F6FA",
            fg="#1F2937"
        ).pack(pady=15)

        # ================= CARD =================
        card = tk.Frame(self, bg="white", bd=1, relief="solid")
        card.pack(pady=10, padx=20, fill="x")

        # GRID CONFIG
        for i in range(2):
            card.grid_columnconfigure(i, weight=1)

        # ================= DATE INPUT =================
        self.start_date = self.create_input(card, "Start Date (YYYY-MM-DD)", 0)
        self.end_date = self.create_input(card, "End Date (YYYY-MM-DD)", 1)

        # ================= STUDENT =================
        tk.Label(card, text="Select Student",
                 font=("Segoe UI", 10, "bold"),
                 bg="white").grid(row=2, column=0, padx=15, pady=10, sticky="w")

        self.student_combo = ttk.Combobox(
            card,
            state="readonly",
            font=("Segoe UI", 10)
        )
        self.student_combo.grid(row=2, column=1, padx=10, pady=10, sticky="ew")

        # ================= BUTTONS =================
        btn_frame = tk.Frame(self, bg="#F3F6FA")
        btn_frame.pack(pady=15)

        self.create_button(btn_frame, "Load Students", "#2563EB", self.load_students, 0)
        self.create_button(btn_frame, "Download CSV", "#16A34A", self.download_csv, 1)
        self.create_button(btn_frame, "Back", "#DC2626",
                           lambda: controller.show_frame("ClassroomFrame"), 2)

        # ================= TABLE =================
        table_frame = tk.Frame(self, bg="white", bd=1, relief="solid")
        table_frame.pack(fill="both", expand=True, padx=20, pady=10)

        columns = ("Student Name", "Student ID", "Time Out", "Fetcher", "Location")

        self.tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings"
        )

        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor="center", width=150)

        self.tree.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

    # ================= HELPERS =================
    def create_input(self, parent, label, row):
        tk.Label(parent, text=label,
                 font=("Segoe UI", 10, "bold"),
                 bg="white").grid(row=row, column=0, padx=15, pady=10, sticky="w")

        entry = tk.Entry(parent, font=("Segoe UI", 10), relief="solid", bd=1)
        entry.grid(row=row, column=1, padx=10, pady=10, sticky="ew")

        return entry

    def create_button(self, parent, text, color, command, col):
        tk.Button(
            parent,
            text=text,
            width=18,
            bg=color,
            fg="white",
            font=("Segoe UI", 10, "bold"),
            bd=0,
            cursor="hand2",
            command=command
        ).grid(row=0, column=col, padx=10)

    def validate_date(self, date_text):
        try:
            datetime.strptime(date_text, "%Y-%m-%d")
            return True
        except ValueError:
            return False

    # ================= LOAD STUDENTS =================
    def load_students(self):
        try:
            teacher = self.controller.current_user.get("username")

            with db_connect() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT DISTINCT student_name
                        FROM history_log
                        WHERE teacher = %s
                        ORDER BY student_name
                    """, (teacher,))

                    students = [row[0] for row in cur.fetchall()]

            self.student_combo["values"] = ["ALL"] + students
            self.student_combo.current(0)

        except Exception as e:
            messagebox.showerror("Error", str(e))

    # ================= DOWNLOAD =================
    def download_csv(self):
        start = self.start_date.get().strip()
        end = self.end_date.get().strip()
        student = self.student_combo.get()

        if not start or not end:
            messagebox.showerror("Error", "Enter dates")
            return

        if not self.validate_date(start) or not self.validate_date(end):
            messagebox.showerror("Error", "Invalid date format")
            return

        try:
            teacher = self.controller.current_user.get("username")

            with db_connect() as conn:
                with conn.cursor() as cur:

                    query = """
                        SELECT student_name, student_id, time_out, fetcher_name, location
                        FROM history_log
                        WHERE teacher = %s
                        AND DATE(time_out) BETWEEN %s AND %s
                    """

                    params = [teacher, start, end]

                    if student and student != "ALL":
                        query += " AND student_name = %s"
                        params.append(student)

                    query += " ORDER BY time_out DESC"

                    cur.execute(query, tuple(params))
                    rows = cur.fetchall()

            # refresh table
            self.tree.delete(*self.tree.get_children())
            for row in rows:
                self.tree.insert("", "end", values=row)

            if not rows:
                messagebox.showinfo("No Data", "No records found")
                return

            file_path = filedialog.asksaveasfilename(defaultextension=".csv")
            if not file_path:
                return

            with open(file_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["Student Name", "Student ID", "Time Out", "Fetcher", "Location"])
                writer.writerows(rows)

            messagebox.showinfo("Success", "Downloaded successfully")

        except Exception as e:
            messagebox.showerror("Error", str(e))
