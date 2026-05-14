import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from tkcalendar import DateEntry
from openpyxl import Workbook
import matplotlib.pyplot as plt
from collections import Counter
from PIL import Image, ImageTk
import io

from utils.database import db_connect


class TeacherDownloadFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#F3F6FA")

        self.controller = controller
        self.all_rows = []
        self.current_photo = None

        # ================= AUTO REFRESH =================
        self.after(3000, self.auto_refresh)  # every 3 seconds

        # ================= TITLE =================
        tk.Label(self, text="📥 Download Student Logs",
                 font=("Segoe UI", 20, "bold"),
                 bg="#F3F6FA").pack(pady=10)

        # ================= TOP =================
        top = tk.Frame(self, bg="white")
        top.pack(fill="x", padx=20, pady=5)

        self.start_date = DateEntry(top, date_pattern='yyyy-mm-dd')
        self.start_date.pack(side="left", padx=5)

        self.end_date = DateEntry(top, date_pattern='yyyy-mm-dd')
        self.end_date.pack(side="left", padx=5)

        self.search_var = tk.StringVar()
        tk.Entry(top, textvariable=self.search_var).pack(side="left", padx=5)
        self.search_var.trace_add("write", self.live_search)

        ttk.Button(top, text="Load", command=self.load_data).pack(side="left", padx=5)
        ttk.Button(top, text="Excel", command=self.export_excel).pack(side="left", padx=5)
        ttk.Button(top, text="Chart", command=self.show_chart).pack(side="left", padx=5)

        # ================= MAIN =================
        main = tk.Frame(self)
        main.pack(fill="both", expand=True)

        # LEFT (DETAILS)
        left = tk.Frame(main, bg="white", width=250)
        left.pack(side="left", fill="y")

        self.detail = {}
        for field in ["Name", "ID", "Time", "Fetcher", "Location"]:
            lbl = tk.Label(left, text=f"{field}: ", anchor="w", bg="white")
            lbl.pack(fill="x", padx=10, pady=5)
            self.detail[field] = lbl

        # RIGHT (TABLE + PHOTO)
        right = tk.Frame(main)
        right.pack(side="right", fill="both", expand=True)

        # PHOTO
        self.photo_label = tk.Label(right, bg="gray", width=200, height=200)
        self.photo_label.pack(pady=10)

        # TABLE
        columns = ("Name", "ID", "Time", "Fetcher", "Location")
        self.tree = ttk.Treeview(right, columns=columns, show="headings")

        for col in columns:
            self.tree.heading(col, text=col)

        self.tree.pack(fill="both", expand=True)

        self.tree.bind("<<TreeviewSelect>>", self.show_details)

    # ================= AUTO REFRESH =================
    def auto_refresh(self):
        self.load_data()
        self.after(3000, self.auto_refresh)

    # ================= LOAD DATA =================
    def load_data(self):
        try:
            teacher = self.controller.current_user.get("username")

            with db_connect() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT student_name, student_id, time_out, fetcher_name, location
                        FROM history_log
                        WHERE teacher=%s
                        ORDER BY time_out DESC
                        LIMIT 50
                    """, (teacher,))

                    self.all_rows = cur.fetchall()

            self.update_table(self.all_rows)

        except Exception as e:
            print(e)

    # ================= TABLE =================
    def update_table(self, rows):
        self.tree.delete(*self.tree.get_children())
        for row in rows:
            self.tree.insert("", "end", values=row)

    # ================= SEARCH =================
    def live_search(self, *args):
        q = self.search_var.get().lower()

        filtered = [
            r for r in self.all_rows
            if any(q in str(x).lower() for x in r)
        ]

        self.update_table(filtered)

    # ================= DETAILS + PHOTO =================
    def show_details(self, event):
        item = self.tree.focus()
        if not item:
            return

        values = self.tree.item(item, "values")

        fields = ["Name", "ID", "Time", "Fetcher", "Location"]
        for i, f in enumerate(fields):
            self.detail[f].config(text=f"{f}: {values[i]}")

        # LOAD PHOTO FROM DATABASE
        try:
            with db_connect() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT photo FROM students
                        WHERE student_id = %s
                    """, (values[1],))

                    result = cur.fetchone()

                    if result and result[0]:
                        image = Image.open(io.BytesIO(result[0]))
                        image = image.resize((200, 200))

                        self.current_photo = ImageTk.PhotoImage(image)
                        self.photo_label.config(image=self.current_photo)
                    else:
                        self.photo_label.config(image="", text="No Photo")

        except Exception as e:
            print("Photo error:", e)

    # ================= EXPORT =================
    def export_excel(self):
        if not self.all_rows:
            return

        file = filedialog.asksaveasfilename(defaultextension=".xlsx")
        if not file:
            return

        wb = Workbook()
        ws = wb.active

        for r in self.all_rows:
            ws.append(r)

        wb.save(file)

    # ================= CHART =================
    def show_chart(self):
        names = [r[0] for r in self.all_rows]
        count = Counter(names)

        plt.bar(count.keys(), count.values())
        plt.xticks(rotation=45)
        plt.show()