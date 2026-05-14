import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
import csv

from utils.database import db_connect


class TeacherDownloadFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#EAF4F4")

        self.controller = controller

        # ================= TITLE =================
        title = tk.Label(
            self,
            text="Download Student Logs",
            font=("Arial", 22, "bold"),
            bg="#EAF4F4",
            fg="#1F2937"
        )
        title.pack(pady=20)

        # ================= MAIN CARD =================
        card = tk.Frame(
            self,
            bg="white",
            bd=1,
            relief="solid"
        )
        card.pack(pady=10, padx=20)

        # ================= DATE SECTION =================
        tk.Label(
            card,
            text="Start Date (YYYY-MM-DD)",
            font=("Arial", 11, "bold"),
            bg="white"
        ).grid(row=0, column=0, padx=15, pady=10, sticky="w")

        self.start_date = tk.Entry(
            card,
            width=25,
            font=("Arial", 11)
        )
        self.start_date.grid(row=0, column=1, pady=10)

        tk.Label(
            card,
            text="End Date (YYYY-MM-DD)",
            font=("Arial", 11, "bold"),
            bg="white"
        ).grid(row=1, column=0, padx=15, pady=10, sticky="w")

        self.end_date = tk.Entry(
            card,
            width=25,
            font=("Arial", 11)
        )
        self.end_date.grid(row=1, column=1, pady=10)

        # ================= STUDENT FILTER =================
        tk.Label(
            card,
            text="Select Student",
            font=("Arial", 11, "bold"),
            bg="white"
        ).grid(row=2, column=0, padx=15, pady=10, sticky="w")

        self.student_combo = ttk.Combobox(
            card,
            width=22,
            state="readonly",
            font=("Arial", 10)
        )
        self.student_combo.grid(row=2, column=1, pady=10)

        # ================= BUTTONS =================
        btn_frame = tk.Frame(self, bg="#EAF4F4")
        btn_frame.pack(pady=20)

        tk.Button(
            btn_frame,
            text="Load Students",
            width=18,
            bg="#2563EB",
            fg="white",
            font=("Arial", 10, "bold"),
            cursor="hand2",
            command=self.load_students
        ).grid(row=0, column=0, padx=10)

        tk.Button(
            btn_frame,
            text="Download CSV",
            width=18,
            bg="#16A34A",
            fg="white",
            font=("Arial", 10, "bold"),
            cursor="hand2",
            command=self.download_csv
        ).grid(row=0, column=1, padx=10)

        tk.Button(
            btn_frame,
            text="Back",
            width=18,
            bg="#DC2626",
            fg="white",
            font=("Arial", 10, "bold"),
            cursor="hand2",
            command=lambda: controller.show_frame("ClassroomFrame")
        ).grid(row=0, column=2, padx=10)

        # ================= TABLE =================
        table_frame = tk.Frame(self, bg="#EAF4F4")
        table_frame.pack(fill="both", expand=True, padx=20, pady=10)

        columns = (
            "Student Name",
            "Student ID",
            "Time Out",
            "Fetcher",
            "Location"
        )

        self.tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            height=12
        )

        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=180)

        scrollbar = ttk.Scrollbar(
            table_frame,
            orient="vertical",
            command=self.tree.yview
        )

        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    # ================= VALIDATE DATE =================
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
                        ORDER BY student_name ASC
                    """, (teacher,))

                    students = [row[0] for row in cur.fetchall()]

            self.student_combo["values"] = ["ALL"] + students
            self.student_combo.current(0)

            messagebox.showinfo(
                "Success",
                "Students loaded successfully!"
            )

        except Exception as e:
            messagebox.showerror("Database Error", str(e))

    # ================= DOWNLOAD CSV =================
    def download_csv(self):

        start = self.start_date.get().strip()
        end = self.end_date.get().strip()
        student = self.student_combo.get()

        # ===== VALIDATION =====
        if not start or not end:
            messagebox.showerror(
                "Input Error",
                "Please enter start and end dates."
            )
            return

        if not self.validate_date(start) or not self.validate_date(end):
            messagebox.showerror(
                "Date Error",
                "Date format must be YYYY-MM-DD"
            )
            return

        try:
            teacher = self.controller.current_user.get("username")

            with db_connect() as conn:
                with conn.cursor() as cur:

                    if student == "ALL" or student == "":
                        query = """
                            SELECT
                                student_name,
                                student_id,
                                time_out,
                                fetcher_name,
                                location
                            FROM history_log
                            WHERE teacher = %s
                            AND DATE(time_out)
                            BETWEEN %s AND %s
                            ORDER BY time_out DESC
                        """

                        cur.execute(query, (teacher, start, end))

                    else:
                        query = """
                            SELECT
                                student_name,
                                student_id,
                                time_out,
                                fetcher_name,
                                location
                            FROM history_log
                            WHERE teacher = %s
                            AND student_name = %s
                            AND DATE(time_out)
                            BETWEEN %s AND %s
                            ORDER BY time_out DESC
                        """

                        cur.execute(query, (
                            teacher,
                            student,
                            start,
                            end
                        ))

                    rows = cur.fetchall()

            # ===== CLEAR TABLE =====
            for item in self.tree.get_children():
                self.tree.delete(item)

            # ===== SHOW DATA =====
            for row in rows:
                self.tree.insert("", "end", values=row)

            if not rows:
                messagebox.showinfo(
                    "No Data",
                    "No records found."
                )
                return

            # ===== SAVE FILE =====
            file_path = filedialog.asksaveasfilename(
                title="Save CSV File",
                defaultextension=".csv",
                filetypes=[("CSV Files", "*.csv")]
            )

            if not file_path:
                return

            with open(file_path, "w", newline="", encoding="utf-8") as file:

                writer = csv.writer(file)

                writer.writerow([
                    "Student Name",
                    "Student ID",
                    "Time Out",
                    "Fetcher",
                    "Location"
                ])

                writer.writerows(rows)

            messagebox.showinfo(
                "Success",
                "CSV downloaded successfully!"
            )

        except Exception as e:
            messagebox.showerror("Error", str(e))