import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime
import csv
import os
import sys

from openpyxl import Workbook
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import matplotlib.pyplot as plt

# ================= DATABASE =================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)
from utils.database import db_connect

class Report(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#e0f7fa")
        self.controller = controller
        self.pack(fill="both", expand=True)

        # ================= HEADER =================
        header = tk.Frame(self, bg="#0047AB", height=70)
        header.pack(fill="x")
        tk.Label(
            header,
            text="DATE-BASED REPORTS",
            font=("Arial", 20, "bold"),
            bg="#0047AB",
            fg="white"
        ).pack(side="left", padx=20, pady=15)

        # ================= FILTER SECTION =================
        content = tk.Frame(self, bg="#e0f7fa")
        content.pack(fill="both", expand=True, padx=15, pady=5)
        
        # Configure content to allow tables to expand
        content.columnconfigure((0, 1), weight=1)
        content.rowconfigure(1, weight=1) # Give the tables frame weight

        filter_card = tk.Frame(content, bg="white", bd=2, relief="groove")
        filter_card.grid(row=0, column=0, columnspan=2, sticky="ew", pady=5, padx=5)

        tk.Label(filter_card, text="From:", bg="white", font=("Arial", 11)).grid(row=0, column=0, padx=5, pady=6)
        self.from_date = tk.Entry(filter_card, width=14, font=("Arial", 10))
        self.from_date.grid(row=0, column=1, pady=6)
        self.from_date.insert(0, "2024-01-01")

        tk.Label(filter_card, text="To:", bg="white", font=("Arial", 11)).grid(row=0, column=2, padx=5)
        self.to_date = tk.Entry(filter_card, width=14, font=("Arial", 10))
        self.to_date.grid(row=0, column=3, pady=6)
        self.to_date.insert(0, datetime.today().strftime("%Y-%m-%d"))

        tk.Button(
            filter_card,
            text="Apply",
            bg="#2196F3",
            fg="white",
            font=("Arial", 10, "bold"),
            width=12,
            relief="raised",
            bd=2,
            command=self.apply_filter
        ).grid(row=0, column=4, padx=10)

        # ================= TABLES =================
        tables = tk.Frame(content, bg="#e0f7fa")
        tables.grid(row=1, column=0, columnspan=2, sticky="nsew", pady=5)
        
        # Ensure tables expand equally
        tables.columnconfigure((0, 1), weight=1)
        tables.rowconfigure((0, 1), weight=1)

        self.student_table = self.create_table(
            tables, "STUDENTS",
            ["ID", "Name", "Grade", "Date"], 0, 0
        )

        self.teacher_table = self.create_table(
            tables, "TEACHERS",
            ["ID", "Name", "Date"], 0, 1
        )

        self.fetcher_table = self.create_table(
            tables, "FETCHERS",
            ["ID", "Fetcher", "Contact", "Date"], 1, 0, colspan=2
        )

        # ================= BUTTONS =================
        # Pack this at the bottom to ensure it's always visible
        btn_frame = tk.Frame(self, bg="#e0f7fa")
        btn_frame.pack(side="bottom", pady=10)

        tk.Button(
            btn_frame,
            text="EXPORT",
            font=("Arial", 11, "bold"),
            bg="#4CAF50",
            fg="white",
            width=16,
            relief="raised",
            bd=2,
            command=self.export_popup
        ).grid(row=0, column=0, padx=8)

        tk.Button(
            btn_frame,
            text="SHOW CHART",
            font=("Arial", 11, "bold"),
            bg="#FF9800",
            fg="white",
            width=16,
            relief="raised",
            bd=2,
            command=self.show_chart
        ).grid(row=0, column=1, padx=8)

        self.apply_filter()

    def create_table(self, parent, title, columns, r, c, colspan=1):
        frame = tk.Frame(parent, bg="white", bd=2, relief="groove")
        frame.grid(row=r, column=c, columnspan=colspan, padx=5, pady=3, sticky="nsew")
        tk.Label(frame, text=title, font=("Arial", 11, "bold"), bg="white").pack(pady=2)

        tree = ttk.Treeview(frame, columns=columns, show="headings", height=5)
        tree.pack(side="left", fill="both", expand=True, padx=5, pady=2)

        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        scrollbar.pack(side="right", fill="y")
        tree.configure(yscrollcommand=scrollbar.set)

        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=100, anchor="center")

        tree.count_var = tk.StringVar(value="Total: 0")
        tk.Label(frame, textvariable=tree.count_var, bg="white", fg="#0047AB", font=("Arial", 9, "bold")).pack(pady=2)
        return tree

    # ================= DATABASE FETCH =================
    def fetch_data(self, query):
        conn = db_connect()
        cur = conn.cursor()
        cur.execute(query)
        data = cur.fetchall()
        conn.close()
        return data

    def get_students(self):
        return self.fetch_data("SELECT ID, Student_name, grade_lvl, created_at FROM student")

    def get_teachers(self):
        return self.fetch_data("SELECT teacher_id,teacher_name, created_at FROM teacher")

    def get_fetchers(self):
        return self.fetch_data("SELECT ID, fetcher_name, contact, created_at FROM fetcher")

    # ================= FILTER =================
    def apply_filter(self):
        for t in (self.student_table, self.teacher_table, self.fetcher_table):
            t.delete(*t.get_children())

        f = datetime.strptime(self.from_date.get(), "%Y-%m-%d").date()
        t = datetime.strptime(self.to_date.get(), "%Y-%m-%d").date()

        self.fill(self.student_table, self.get_students(), f, t)
        self.fill(self.teacher_table, self.get_teachers(), f, t)
        self.fill(self.fetcher_table, self.get_fetchers(), f, t)

    def fill(self, table, data, f, t):
        count = 0
        for row in data:
            d = row[-1]
            if isinstance(d, str):
                d = datetime.strptime(d, "%Y-%m-%d").date()
            if f <= d <= t:
                table.insert("", "end", values=row)
                count += 1
        table.count_var.set(f"Total: {count}")

    # ================= EXPORT =================
    def export_popup(self):
        win = tk.Toplevel(self)
        win.title("Export Reports")
        win.geometry("320x350")
        win.resizable(False, False)
        win.configure(bg="white")
        win.grab_set()  # Focus on this window

        # Styling headers
        lbl_style = {"bg": "white", "font": ("Arial", 10, "bold"), "fg": "#333"}

        tk.Label(win, text="1. SELECT DATA", **lbl_style).pack(pady=(15, 5))
        
        choice = tk.StringVar(value="students")
        choices_frame = tk.Frame(win, bg="white")
        choices_frame.pack()
        
        # Added "All Reports" option
        options = [("Students", "students"), ("Teachers", "teachers"), 
                   ("Fetchers", "fetchers"), ("All Reports", "all")]
        
        for text, mode in options:
            tk.Radiobutton(choices_frame, text=text, variable=choice, value=mode, 
                           bg="white", activebackground="white", font=("Arial", 10)).pack(anchor="w")

        tk.Label(win, text="2. SELECT FORMAT", **lbl_style).pack(pady=(15, 5))
        
        fmt = tk.StringVar(value="csv")
        formats_frame = tk.Frame(win, bg="white")
        formats_frame.pack()
        
        for f_text, f_mode in [("CSV", "csv"), ("Excel", "excel"), ("PDF", "pdf")]:
            tk.Radiobutton(formats_frame, text=f_text, variable=fmt, value=f_mode, 
                           bg="white", activebackground="white").pack(side="left", padx=10)

        # Export Button
        tk.Button(
            win,
            text="START EXPORT",
            bg="#0047AB",
            fg="white",
            font=("Arial", 11, "bold"),
            relief="flat",
            width=20,
            cursor="hand2",
            command=lambda: self.export_logic(choice.get(), fmt.get(), win)
        ).pack(pady=25)
        
    def export_logic(self, choice, fmt, win):
        # Define which tables to process
        data_map = {
            "students": (self.student_table, "Student_Report"),
            "teachers": (self.teacher_table, "Teacher_Report"),
            "fetchers": (self.fetcher_table, "Fetcher_Report")
        }

        if choice == "all":
            # Select folder for multiple files
            folder_path = filedialog.askdirectory(title="Select Folder to Save Reports")
            if not folder_path: return
            
            for key in data_map:
                table, default_name = data_map[key]
                full_path = os.path.join(folder_path, f"{default_name}.{fmt}")
                self.save_file(table, fmt, full_path)
        else:
            # Single file save
            table, default_name = data_map[choice]
            path = filedialog.asksaveasfilename(
                defaultextension=f".{fmt}",
                initialfile=default_name,
                filetypes=[(fmt.upper(), f"*.{fmt}")]
            )
            if not path: return
            self.save_file(table, fmt, path)

        win.destroy()
        messagebox.showinfo("Export Success", f"Reports have been saved as {fmt.upper()}.")

    def save_file(self, table, fmt, path):
        """Helper to handle the actual writing logic"""
        headers = table["columns"]
        rows = [table.item(i, "values") for i in table.get_children()]

        if fmt == "csv":
            with open(path, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(headers)
                writer.writerows(rows)

        elif fmt == "excel":
            wb = Workbook()
            ws = wb.active
            ws.append(headers)
            for r in rows:
                ws.append(r)
            wb.save(path)

        elif fmt == "pdf":
            pdf = canvas.Canvas(path, pagesize=letter)
            y = 750
            pdf.setFont("Helvetica-Bold", 12)
            pdf.drawString(40, y, f"Report Exported on {datetime.now().strftime('%Y-%m-%d')}")
            y -= 30
            
            # Draw Headers
            pdf.setFont("Helvetica-Bold", 10)
            pdf.drawString(40, y, " | ".join(headers))
            pdf.line(40, y-5, 550, y-5)
            y -= 25
            
            # Draw Rows
            pdf.setFont("Helvetica", 9)
            for r in rows:
                if y < 50:
                    pdf.showPage()
                    y = 750
                pdf.drawString(40, y, " | ".join(map(str, r)))
                y -= 18
            pdf.save()

    def export(self, choice, fmt, win):
        table = {
            "students": self.student_table,
            "teachers": self.teacher_table,
            "fetchers": self.fetcher_table
        }[choice]

        path = filedialog.asksaveasfilename(defaultextension=f".{fmt}")
        if not path:
            return

        headers = table["columns"]
        rows = [table.item(i, "values") for i in table.get_children()]

        if fmt == "csv":
            with open(path, "w", newline="") as f:
                csv.writer(f).writerows([headers] + rows)

        elif fmt == "excel":
            wb = Workbook()
            ws = wb.active
            ws.append(headers)
            for r in rows:
                ws.append(r)
            wb.save(path)

        elif fmt == "pdf":
            pdf = canvas.Canvas(path, pagesize=letter)
            y = 750
            pdf.setFont("Helvetica-Bold", 10)
            pdf.drawString(40, y, " | ".join(headers))
            y -= 25
            pdf.setFont("Helvetica", 9)
            for r in rows:
                if y < 50:
                    pdf.showPage()
                    y = 750
                pdf.drawString(40, y, " | ".join(map(str, r)))
                y -= 18
            pdf.save()

        win.destroy()
        messagebox.showinfo("Success", "Export completed")

    # ================= CHART =================
    def show_chart(self):
        labels = ["Students", "Teachers", "Fetchers"]
        values = [
            len(self.student_table.get_children()),
            len(self.teacher_table.get_children()),
            len(self.fetcher_table.get_children())
        ]
        plt.figure(figsize=(6,4))
        plt.bar(labels, values, color=["#4CAF50", "#2196F3", "#FF9800"])
        plt.title("Total Records", fontsize=14, fontweight="bold")
        plt.ylabel("Count", fontsize=12)
        plt.show()
