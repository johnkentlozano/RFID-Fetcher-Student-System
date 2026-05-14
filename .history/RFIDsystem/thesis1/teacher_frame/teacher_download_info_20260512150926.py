import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from tkcalendar import DateEntry
from openpyxl import Workbook
import matplotlib.pyplot as plt
from collections import Counter

from utils.database import db_connect


class TeacherDownloadFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#F3F6FA")

        self.controller = controller
        self.all_rows = []

        # ================= STYLE (UNCHANGED) =================
        style = ttk.Style()
        style.theme_use("default")

        style.configure("Treeview", rowheight=28, font=("Segoe UI", 10))
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))

        # ================= EVERYTHING UI UNCHANGED =================
        tk.Label(self, text="📥 Download Student Logs",
                 font=("Segoe UI", 22, "bold"),
                 bg="#F3F6FA", fg="#1F2937").pack(pady=15)

        card = tk.Frame(self, bg="white", bd=1, relief="solid")
        card.pack(pady=10, padx=20, fill="x")

        for i in range(2):
            card.grid_columnconfigure(i, weight=1)

        tk.Label(card, text="Start Date", bg="white").grid(row=0, column=0)
        self.start_date = DateEntry(card, date_pattern='yyyy-mm-dd')
        self.start_date.grid(row=0, column=1, sticky="ew")

        tk.Label(card, text="End Date", bg="white").grid(row=1, column=0)
        self.end_date = DateEntry(card, date_pattern='yyyy-mm-dd')
        self.end_date.grid(row=1, column=1, sticky="ew")

        tk.Label(card, text="Live Search", bg="white").grid(row=2, column=0)
        self.search_var = tk.StringVar()
        tk.Entry(card, textvariable=self.search_var).grid(row=2, column=1)
        self.search_var.trace_add("write", self.live_search)

        tk.Label(card, text="Select Student", bg="white").grid(row=3, column=0)
        self.student_combo = ttk.Combobox(card, state="readonly")
        self.student_combo.grid(row=3, column=1)

        btn_frame = tk.Frame(self, bg="#F3F6FA")
        btn_frame.pack(pady=10)

        self.create_button(btn_frame, "Load Students", "#2563EB", self.load_students, 0)
        self.create_button(btn_frame, "Load Data", "#9333EA", self.load_data, 1)
        self.create_button(btn_frame, "Export Excel", "#16A34A", self.export_excel, 2)
        self.create_button(btn_frame, "Show Chart", "#F59E0B", self.show_chart, 3)

        main_frame = tk.Frame(self, bg="#F3F6FA")
        main_frame.pack(fill="both", expand=True)

        self.tree = ttk.Treeview(main_frame,
                                 columns=("Student Name", "Student ID", "Time Out", "Fetcher", "Location"),
                                 show="headings")

        for col in self.tree["columns"]:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor="center", width=150)

        self.tree.pack(fill="both", expand=True)

        self.tree.bind("<<TreeviewSelect>>", self.show_details)

    # ================= 🔥 FIX 1: LOAD STUDENTS =================
    def load_students(self):
        try:
            employee_id = self.controller.current_user.get("employee_id")

            with db_connect() as conn:
                with conn.cursor() as cur:

                    cur.execute("""
                        SELECT DISTINCT student_name
                        FROM history_log
                        WHERE teacher = %s
                    """, (employee_id,))

                    students = [row[0] for row in cur.fetchall()]

            self.student_combo["values"] = ["ALL"] + students
            self.student_combo.current(0)

        except Exception as e:
            messagebox.showerror("Error", str(e))

    # ================= 🔥 FIX 2: LOAD DATA =================
    def load_data(self):
        try:
            start = self.start_date.get()
            end = self.end_date.get()
            student = self.student_combo.get()

            employee_id = self.controller.current_user.get("employee_id")

            with db_connect() as conn:
                with conn.cursor() as cur:

                    query = """
                        SELECT student_name, student_id, time_out, fetcher_name, location
                        FROM history_log
                        WHERE teacher = %s
                        AND DATE(time_out) BETWEEN %s AND %s
                    """

                    params = [employee_id, start, end]

                    if student and student != "ALL":
                        query += " AND student_name = %s"
                        params.append(student)

                    cur.execute(query, tuple(params))
                    self.all_rows = cur.fetchall()

            self.update_table(self.all_rows)

        except Exception as e:
            messagebox.showerror("Error", str(e))

    # ================= UI FUNCTIONS (UNCHANGED) =================
    def create_button(self, parent, text, color, command, col):
        tk.Button(parent, text=text, bg=color, fg="white",
                  command=command).grid(row=0, column=col, padx=5)

    def update_table(self, rows):
        self.tree.delete(*self.tree.get_children())
        for row in rows:
            self.tree.insert("", "end", values=row)

    def live_search(self, *args):
        q = self.search_var.get().lower()
        filtered = [r for r in self.all_rows if any(q in str(c).lower() for c in r)]
        self.update_table(filtered)

    def show_details(self, event):
        pass

    def export_excel(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".xlsx")
        if not file_path:
            return

        wb = Workbook()
        ws = wb.active
        ws.append(["Student Name", "Student ID", "Time Out", "Fetcher", "Location"])

        for r in self.all_rows:
            ws.append(r)

        wb.save(file_path)
        messagebox.showinfo("Success", "Exported!")

    def show_chart(self):
        if not self.all_rows:
            return

        names = [r[0] for r in self.all_rows]
        c = Counter(names)

        plt.bar(c.keys(), c.values())
        plt.xticks(rotation=45)
        plt.title("Student Fetch Frequency")
        plt.tight_layout()
        plt.show()