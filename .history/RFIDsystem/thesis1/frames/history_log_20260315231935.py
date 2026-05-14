import tkinter as tk
from tkinter import messagebox, ttk
from datetime import datetime, timedelta
import os
import sys

# ================= PATH SETUP =================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from utils.database import db_connect

class RFIDHistory(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#b2e5ed")
        self.controller = controller

        # ================= HEADER =================
        header = tk.Frame(self, bg="#0047AB", height=60)
        header.pack(fill="x")
        tk.Label(header, text="HISTORY FETCH & RECALL", font=("Arial", 18, "bold"), 
                 bg="#0047AB", fg="white").pack(pady=10)

        # ================= SEARCH PANEL =================
        search_frame = tk.Frame(self, bg="#b2e5ed", pady=10)
        search_frame.pack(fill="x", padx=20)

        tk.Label(search_frame, text="Student/Fetcher:", bg="#b2e5ed", font=("Arial", 10, "bold")).pack(side="left", padx=5)
        self.search_var = tk.StringVar()
        tk.Entry(search_frame, textvariable=self.search_var, width=20).pack(side="left", padx=5)

        tk.Label(search_frame, text="Date (YYYY-MM-DD):", bg="#b2e5ed", font=("Arial", 10, "bold")).pack(side="left", padx=5)
        self.date_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        tk.Entry(search_frame, textvariable=self.date_var, width=15).pack(side="left", padx=5)

        tk.Button(search_frame, text="SEARCH", command=self.load_history_data, 
                  bg="#2196F3", fg="white", font=("Arial", 9, "bold")).pack(side="left", padx=10)
        
        tk.Button(search_frame, text="RESET", command=self.reset_filters, 
                  bg="#f44336", fg="white", font=("Arial", 9, "bold")).pack(side="left")

        # ================= TABLE SETUP =================
        table_frame = tk.Frame(self, bg="white", bd=1, relief="solid")
        table_frame.pack(expand=True, fill="both", padx=20, pady=10)

        cols = ("ID", "Fetcher", "Student", "Grade", "Teacher", "Gate", "Date & Time")
        self.table = ttk.Treeview(table_frame, columns=cols, show="headings")
        
        widths = {"ID": 50, "Fetcher": 140, "Student": 140, "Grade": 80, "Teacher": 140, "Gate": 80, "Date & Time": 160}
        for col in cols:
            self.table.heading(col, text=col.upper())
            self.table.column(col, anchor="center", width=widths.get(col, 100))
        
        self.table.pack(side="left", expand=True, fill="both")
        
        scroller = ttk.Scrollbar(table_frame, orient="vertical", command=self.table.yview)
        self.table.configure(yscrollcommand=scroller.set)
        scroller.pack(side="right", fill="y")

        self.load_history_data()
        self.auto_refresh()

    def reset_filters(self):
        self.search_var.set("")
        self.date_var.set(datetime.now().strftime("%Y-%m-%d"))
        self.load_history_data()

    def load_history_data(self):
        self.table.delete(*self.table.get_children())
        name_filter = self.search_var.get().strip()
        date_filter = self.date_var.get().strip()

        # Define a visual style for Overrides
        self.table.tag_configure('override_row', background='#fff3cd', foreground='#856404')

        try:
            with db_connect() as conn:
                with conn.cursor() as cur:
                    sql = """SELECT id, fetcher_name, student_name, grade, teacher, location, time_out 
                             FROM history_log 
                             WHERE DATE(time_out) = %s"""
                    params = [date_filter]

                    if name_filter:
                        sql += " AND (student_name LIKE %s OR fetcher_name LIKE %s OR teacher LIKE %s)"
                        params.extend([f"%{name_filter}%", f"%{name_filter}%", f"%{name_filter}%"])

                    sql += " ORDER BY time_out DESC"
                    
                    cur.execute(sql, tuple(params))
                    for row in cur.fetchall():
                        display_row = list(row)
                        display_row[6] = row[6].strftime('%Y-%m-%d %I:%M %p')
                        
                        # Apply the "override_row" tag if the fetcher name contains 'OVERRIDE'
                        if "OVERRIDE" in str(display_row[1]):
                            self.table.insert("", "end", values=display_row, tags=('override_row',))
                        else:
                            self.table.insert("", "end", values=display_row)
        except Exception as e:
            print(f"Error loading history: {e}")

    def save_log(self, f_name, s_name, s_id, grade, teacher, gate, is_override=False):
        # If it's an override, we prefix the name so it's clear in the history table
        final_fetcher_name = f"⭐ OVERRIDE: {f_name}" if is_override else f_name
        
        try:
            with db_connect() as conn:
                with conn.cursor() as cur:
                    # 1. INSERT NEW RECORD
                    cur.execute("""INSERT INTO history_log 
                                    (fetcher_name, student_name, student_id, grade, teacher, location, time_out) 
                                    VALUES (%s, %s, %s, %s, %s, %s, NOW())""", 
                                    (final_fetcher_name, s_name, s_id, grade, teacher, gate))

                    # 2. AUTOMATIC CLEANUP (Keep only 7 days)
                    cur.execute("DELETE FROM history_log WHERE time_out < NOW() - INTERVAL 7 DAY")

                    conn.commit()
            
            # Refresh table if the frame is active
            if self.winfo_viewable():
                self.load_history_data()
        except Exception as e:
            messagebox.showerror("Database Error", f"Could not save: {e}")

    def auto_refresh(self):
        
        if not self.search_var.get() and self.winfo_viewable():
            self.load_history_data()
        self.after(10000, self.auto_refresh)