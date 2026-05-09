import tkinter as tk
from tkinter import messagebox, ttk
import os, sys

# Ensure utility imports work
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

from utils.database import db_connect

class OverrideFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#b2e5ed") # Keeping your light blue theme
        self.controller = controller
        self.rfid_validator = self.register(self.validate_rfid)
        self.mode = None  # "add" or "edit" logic from Admin frame

        # --- UI Header ---
        header = tk.Frame(self, bg="#0047AB", height=60)
        header.pack(fill="x")
        tk.Label(header, text="MASTER RFID MANAGEMENT", font=("Arial", 18, "bold"), 
                 bg="#0047AB", fg="white").pack(pady=10)

        # --- Main Layout ---
        main_container = tk.Frame(self, bg="#b2e5ed")
        main_container.pack(fill="both", expand=True, padx=20, pady=20)

        # --- LEFT SIDE: Form ---
        self.form_container = tk.Frame(main_container, bg="white", padx=20, pady=20, 
                                       highlightthickness=2, highlightbackground="#CCCCCC")
        self.form_container.pack(side="left", fill="y", padx=(0, 20))

        self.mode_label = tk.Label(self.form_container, text="IDLE: SELECT ACTION", 
                                    font=("Arial", 10, "bold"), bg="#f5f5f5", fg="#757575", pady=5)
        self.mode_label.pack(fill="x", pady=(0, 15))

        tk.Label(self.form_container, text="Teacher Employee ID:", bg="white", font=("Arial", 9, "bold")).pack(anchor="w")
        self.emp_id_entry = tk.Entry(self.form_container, font=("Arial", 11), width=25, bd=1, relief="solid")
        self.emp_id_entry.pack(pady=(5, 15), ipady=3)

        tk.Label(self.form_container, text="RFID UID (Tap Card):", bg="white", 
                 font=("Arial", 9, "bold"), fg="#0047AB").pack(anchor="w")
        self.rfid_entry = tk.Entry(
            self.form_container,
            font=("Arial", 11),
            width=25,
            bd=1,
            relief="solid",
            justify="center",
            validate="key",
            validatecommand=(self.rfid_validator, "%P")
        )
        self.rfid_entry.pack(pady=(5, 10), ipady=3)
        self.rfid_entry.bind("<Return>", lambda e: self.handle_save())

        # Action Buttons (Mirrored from Admin Management)
        self.add_btn = tk.Button(self.form_container, text="➕ ADD NEW", command=self.start_add,
                                 bg="#4CAF50", fg="white", font=("Arial", 9, "bold"), width=20, pady=6)
        self.add_btn.pack(pady=3)

        self.edit_btn = tk.Button(self.form_container, text="✏ EDIT SELECTED", command=self.start_edit,
                                  bg="#2196F3", fg="white", font=("Arial", 9, "bold"), width=20, pady=6)
        self.edit_btn.pack(pady=3)

        self.save_btn = tk.Button(self.form_container, text="💾 SAVE CHANGES", command=self.handle_save,
                                  bg="#FF9800", fg="white", font=("Arial", 9, "bold"), width=20, pady=6)
        self.save_btn.pack(pady=3)

        self.del_btn = tk.Button(self.form_container, text="🗑 DELETE", command=self.handle_delete,
                                 bg="#f44336", fg="white", font=("Arial", 9, "bold"), width=20, pady=6)
        self.del_btn.pack(pady=3)

        self.cancel_btn = tk.Button(self.form_container, text="✖ CANCEL", command=self.clear_form,
                                    bg="#757575", fg="white", font=("Arial", 9, "bold"), width=20, pady=6)

        # --- RIGHT SIDE: List ---
        list_container = tk.Frame(main_container, bg="white", padx=10, pady=10, 
                                  highlightthickness=1, highlightbackground="#CCCCCC")
        list_container.pack(side="right", fill="both", expand=True)

        list_header = tk.Frame(list_container, bg="white")
        list_header.pack(fill="x", pady=(0, 10))
        tk.Label(list_header, text="Registered Master Overrides", font=("Arial", 11, "bold"), bg="white").pack(side="left")
        
        tk.Button(list_header, text="✅ ACTIVATE", bg="#2196F3", fg="white", font=("Arial", 8, "bold"), 
                  command=lambda: self.toggle_status("Active")).pack(side="right", padx=2)
        tk.Button(list_header, text="🚫 DEACTIVATE", bg="#FF9800", fg="white", font=("Arial", 8, "bold"), 
                  command=lambda: self.toggle_status("Deactivated")).pack(side="right", padx=2)

        self.tree = ttk.Treeview(list_container, columns=("EID", "Name", "UID", "Status"), show="headings", height=15)
        self.tree.heading("EID", text="Emp ID"); self.tree.heading("Name", text="Teacher Name")
        self.tree.heading("UID", text="RFID UID"); self.tree.heading("Status", text="Status")
        self.tree.column("EID", width=70, anchor="center")
        self.tree.column("Status", width=100, anchor="center")
        self.tree.pack(fill="both", expand=True)
        
        self.refresh_list()
        self.clear_form()

    # ---------------- UI STATE CONTROL (Applied from Admin Code) ----------------
    def set_ui_state(self, state):
        if state == "idle":
            self.emp_id_entry.config(state="disabled")
            self.rfid_entry.config(state="disabled")
            self.save_btn.config(state="disabled")
            self.cancel_btn.pack_forget()
            self.add_btn.config(state="normal")
            self.edit_btn.config(state="normal")
            self.del_btn.config(state="normal")
            self.tree.config(selectmode="browse")
        elif state == "active":
            self.emp_id_entry.config(state="normal")
            self.rfid_entry.config(state="normal")
            self.save_btn.config(state="normal")
            self.cancel_btn.pack(after=self.save_btn, pady=3)
            self.add_btn.config(state="disabled")
            self.edit_btn.config(state="disabled")
            self.del_btn.config(state="disabled")
            self.tree.config(selectmode="none")

    # ---------------- ACTIONS ----------------
    def start_add(self):
        self.mode = "add"
        self.set_ui_state("active")
        self.emp_id_entry.delete(0, tk.END)
        self.rfid_entry.delete(0, tk.END)
        self.mode_label.config(text="➕ ADDING NEW TEACHER", bg="#e8f5e9", fg="#2e7d32")
        self.emp_id_entry.focus_set()

    def start_edit(self):
        selected = self.tree.focus()
        if not selected:
            messagebox.showwarning("Selection Required", "Please select a record.")
            return
        values = self.tree.item(selected, "values")
        self.mode = "edit"
        self.set_ui_state("active")

        self.emp_id_entry.config(state="normal")
        self.emp_id_entry.delete(0, tk.END)
        self.emp_id_entry.insert(0, values[0])
        self.emp_id_entry.config(state="readonly")

        self.rfid_entry.delete(0, tk.END)
        self.rfid_entry.insert(0, values[2])

        self.mode_label.config(text=f"✏️ EDITING: {values[1]}", bg="#fff3e0", fg="#e65100")
        self.rfid_entry.focus_set()

    def clear_form(self):
        self.mode = None
        self.emp_id_entry.config(state="normal")
        self.emp_id_entry.delete(0, tk.END)
        self.rfid_entry.config(state="normal")
        self.rfid_entry.delete(0, tk.END)
        self.mode_label.config(text="IDLE: SELECT ACTION", bg="#f5f5f5", fg="#757575")
        self.set_ui_state("idle")

    def handle_save(self):
        eid = self.emp_id_entry.get().strip()
        uid = self.rfid_entry.get().strip()
        
        if self.mode not in ("add", "edit"):
            messagebox.showwarning("Error", "Invalid operation.")
            return
        
        if not eid or not uid:
            messagebox.showwarning("Input Error", "Teacher ID and RFID UID are required.")
            return

        try:
            with db_connect() as conn:
                with conn.cursor() as cur:
                    # Verify Teacher Role
                    cur.execute("SELECT username FROM users WHERE employee_id=%s AND role='Teacher'", (eid,))
                    if not cur.fetchone():
                        messagebox.showerror("Error", f"ID {eid} is not a registered Teacher.")
                        return

                    # Duplicate RFID check
                    cur.execute("SELECT employee_id FROM teacher_rfid_registration WHERE rfid_uid=%s AND employee_id != %s", (uid, eid))
                    if cur.fetchone():
                        messagebox.showerror("Duplicate RFID", "This card is already assigned to someone else.")
                        return

                    if self.mode == "add":
                        cur.execute("SELECT employee_id FROM teacher_rfid_registration WHERE employee_id=%s", (eid,))
                        if cur.fetchone():
                            messagebox.showerror("Error", "Teacher already registered. Use Edit instead.")
                            return
                        cur.execute("INSERT INTO teacher_rfid_registration (employee_id, rfid_uid, status) VALUES (%s, %s, 'Active')", (eid, uid))
                    else:  
                        cur.execute("UPDATE teacher_rfid_registration SET rfid_uid=%s WHERE employee_id=%s", (uid, eid))
                    
                    conn.commit()
            messagebox.showinfo("Success", "Teacher access updated.")
            self.refresh_list()
            self.clear_form()
        except Exception as e:
            messagebox.showerror("Database Error", str(e))

    def refresh_list(self):
        self.tree.delete(*self.tree.get_children())
        try:
            with db_connect() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT t.employee_id, u.username, t.rfid_uid, t.status 
                        FROM teacher_rfid_registration t
                        JOIN users u ON t.employee_id = u.employee_id
                        ORDER BY u.username ASC
                    """)
                    for row in cur.fetchall():
                        tag = 'active' if row[3] == 'Active' else 'inactive'
                        self.tree.insert("", "end", values=row, tags=(tag,))
            self.tree.tag_configure('active', foreground='green')
            self.tree.tag_configure('inactive', foreground='red')
        except Exception as e:
            print(f"List Refresh Error: {e}")

    def handle_delete(self):
        selected = self.tree.focus()
        if not selected:
            messagebox.showwarning("Warning", "Please select a record to delete.")
            return

        eid = self.tree.item(selected, "values")[0]
        confirm = messagebox.askyesno("Confirm", "Are you sure you want to delete?")
        if not confirm: return

        try:
            with db_connect() as conn:
                with conn.cursor() as cur:
                    cur.execute("DELETE FROM teacher_rfid_registration WHERE employee_id=%s", (eid,))
                    conn.commit()
            messagebox.showinfo("Success", "Record deleted.")
            self.refresh_list()
            self.clear_form()
        except Exception as e:
            messagebox.showerror("Error", str(e))  

    def toggle_status(self, new_status):
        selected = self.tree.focus()
        if not selected: return
        eid = self.tree.item(selected, "values")[0]
        try:
            with db_connect() as conn:
                with conn.cursor() as cur:
                    cur.execute("UPDATE teacher_rfid_registration SET status=%s WHERE employee_id=%s", (new_status, eid))
                    conn.commit()
            self.refresh_list()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def handle_rfid_tap(self, uid):
        focused = self.focus_get()
        if focused == self.rfid_entry:
            self.rfid_entry.delete(0, tk.END)
            self.rfid_entry.insert(0, uid)

    def validate_rfid(self, value):
        return " " not in value