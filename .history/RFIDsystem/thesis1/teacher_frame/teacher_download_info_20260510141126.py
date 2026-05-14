import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import csv
from utils.database import db_connect


class TeacherDownloadFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#F0F4F8")
        self.controller = controller

        tk.Label(self, text="Download Student Logs", font=("Arial", 18, "bold")).pack(pady=20)

        # ===== DATE INPUT =====
        form = tk.Frame(self, bg="#F0F4F8")
        form.pack(pady=10)

        tk.Label(form, text="Start Date (YYYY-MM-DD):").grid(row=0, column=0, padx=10)
        self.start_date = tk.Entry(form)
        self.start_date.grid(row=0, column=1)

        tk.Label(form, text="End Date (YYYY-MM-DD):").grid(row=1, column=0, padx=10)
        self.end_date = tk.Entry(form)
        self.end_date.grid(row=1, column=1)

        # ===== STUDENT FILTER =====
        tk.Label(form, text="Select Student (Optional):").grid(row=2, column=0, padx=10)

        self.student_combo = ttk.Combobox(form, state="readonly")
        self.student_combo.grid(row=2, column=1)

        tk.Button(
            self,
            text="Load Students",
            command=self.load_students
        ).pack(pady=5)

        # ===== DOWNLOAD BUTTON =====
        tk.Button(
            self,
            text="Download CSV",
            bg="#4CAF50",
            fg="white",
            command=self.download_csv
        ).pack(pady=20)

        tk.Button(
            self,
            text="Back",
            command=lambda: controller.show_frame("ClassroomFrame")
        ).pack()

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
            messagebox.showerror("Error", "Enter date range")
            return

        try:
            teacher = self.controller.current_user.get("username")

            with db_connect() as conn:
                with conn.cursor() as cur:

                    if student == "ALL" or not student:
                        query = """
                            SELECT student_name, student_id, time_out, fetcher_name, location
                            FROM history_log
                            WHERE teacher = %s AND DATE(time_out) BETWEEN %s AND %s
                        """
                        cur.execute(query, (teacher, start, end))
                    else:
                        query = """
                            SELECT student_name, student_id, time_out, fetcher_name, location
                            FROM history_log
                            WHERE teacher = %s AND student_name = %s
                            AND DATE(time_out) BETWEEN %s AND %s
                        """
                        cur.execute(query, (teacher, student, start, end))

                    rows = cur.fetchall()

            if not rows:
                messagebox.showinfo("No Data", "No records found")
                return

            # ===== SAVE FILE =====
            file_path = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV File", "*.csv")]
            )

            if not file_path:
                return

            with open(file_path, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["Student Name", "ID", "Time", "Fetcher", "Location"])
                writer.writerows(rows)

            messagebox.showinfo("Success", "File downloaded successfully!")

        except Exception as e:
            messagebox.showerror("Error", str(e))