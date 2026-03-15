import tkinter as tk
from tkinter import messagebox, ttk
import os
import sys

# Ensure utility imports work
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

from utils.database import db_connect

class OverrideFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#b2e5ed")
        self.controller = controller
        self.rfid_validator = self.register(self.validate_rfid)
        self.editing_mode = False 
        
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

        # Edit Mode Indicator
        self.mode_label = tk.Label(self.form_container, text="🆕 NEW REGISTRATION", 
                                   font=("Arial", 10, "bold"), bg="#e8f5e9", fg="#2e7d32", pady=5)
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

        # Buttons
        self.save_btn = tk.Button(self.form_container, text="➕ REGISTER CARD", command=self.handle_save, 
                                  bg="#4CAF50", fg="white", font=("Arial", 9, "bold"), width=20, pady=8, bd=0)
        self.save_btn.pack(pady=5)

        self.edit_btn = tk.Button(
            self.form_container,
            text="✏️ EDIT",
            command=self.enable_edit_mode,
            bg="#2196F3",
            fg="white",
            font=("Arial", 9, "bold"),
            width=20,
            pady=8,
            bd=0
        )
        self.edit_btn.pack(pady=5)
        
        # Initialize Cancel Button (Hidden by default)
        self.cancel_btn = tk.Button(self.form_container, text="✖ CANCEL EDIT", command=self.clear_form, 
                                    bg="#757575", fg="white", font=("Arial", 9, "bold"), width=20, pady=5, bd=0)
        
        self.del_btn = tk.Button(self.form_container, text="🗑️ DELETE RECORD", command=self.handle_delete, 
                                 bg="#f44336", fg="white", font=("Arial", 9, "bold"), width=20, pady=8, bd=0)
        self.del_btn.pack(pady=5)

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
        
        self.tree.bind("<<TreeviewSelect>>", self.on_item_select)
        self.refresh_list()
        
        # SET INITIAL FOCUS so RFID scanning works immediately
        self.emp_id_entry.focus_set()

    # --- KEY FIXES ---

    def handle_save(self):
        eid = self.emp_id_entry.get().strip()
        uid = self.rfid_entry.get().strip()

        if not eid or not uid:
            messagebox.showwarning("Input Error", "ID and RFID are required.")
            return

        try:
            with db_connect() as conn:
                with conn.cursor() as cur:
                    # 1. Check if Teacher exists in main users table
                    cur.execute("SELECT username FROM users WHERE employee_id = %s AND role = 'Teacher'", (eid,))
                    teacher_exists = cur.fetchone()
                    
                    if not teacher_exists:
                        messagebox.showerror("Error", f"Employee ID {eid} is not a registered Teacher.")
                        return

                    # --- NEW: BLOCK REGISTRATION IF ALREADY EXISTS ---
                    if not self.editing_mode: # Only check if we are creating a NEW record
                        cur.execute("SELECT employee_id FROM teacher_rfid_registration WHERE employee_id = %s", (eid,))
                        if cur.fetchone():
                            messagebox.showwarning("Already Registered", 
                                f"Teacher with ID {eid} is already registered.\nUse 'Edit' to change their RFID.")
                            return

                    # 2. Duplicate RFID check (Is this card used by someone else?)
                    cur.execute("SELECT employee_id FROM teacher_rfid_registration WHERE rfid_uid = %s AND employee_id != %s", (uid, eid))
                    if cur.fetchone():
                        messagebox.showerror("Duplicate RFID", "This card is already assigned to another teacher.")
                        return

                    # 3. Save Logic
                    if self.editing_mode:
                        confirm = messagebox.askyesno(
                            "Confirm Update",
                            "Are you sure you want to update this RFID?"
                        )

                        if not confirm:
                            return
                        cur.execute("""
                            UPDATE teacher_rfid_registration 
                            SET rfid_uid = %s 
                            WHERE employee_id = %s
                        """, (uid, eid))
                    else:
                        cur.execute("""
                            INSERT INTO teacher_rfid_registration (employee_id, rfid_uid, status) 
                            VALUES (%s, %s, 'Active')
                        """, (eid, uid))
                    
                    conn.commit()

            messagebox.showinfo("Success", "Registration processed successfully.")
            self.refresh_list()
            self.clear_form()
        except Exception as e:
            messagebox.showerror("Database Error", str(e))

    def on_item_select(self, event):
        selected_items = self.tree.selection()
        if not selected_items:
            return

        selected = selected_items[0]

        values = self.tree.item(selected, "values")

        teacher_id = values[0]
        teacher_name = values[1]
        uid = values[2]

        # VIEW MODE
        self.editing_mode = False

        self.mode_label.config(
            text=f"👁 VIEWING: {teacher_name}",
            bg="#e3f2fd",
            fg="#0d47a1"
        )

        # Show values in input boxes
        self.emp_id_entry.config(state="normal")
        self.rfid_entry.config(state="normal")

        self.emp_id_entry.delete(0, tk.END)
        self.emp_id_entry.insert(0, teacher_id)

        self.rfid_entry.delete(0, tk.END)
        self.rfid_entry.insert(0, uid)

        # Lock them in view mode
        self.emp_id_entry.config(state="readonly")
        self.rfid_entry.config(state="readonly")

        # Show edit button
        self.edit_btn.pack(pady=5)

    def enable_edit_mode(self):

        self.editing_mode = True

        self.mode_label.config(
            text="✏️ EDIT MODE",
            bg="#fff3e0",
            fg="#e65100"
        )

        self.rfid_entry.config(state="normal")

        # Hide edit button
        self.edit_btn.pack_forget()

        # Change register button
        self.save_btn.config(
            text="💾 UPDATE CHANGES",
            bg="#FF9800"
        )

        # Show cancel button
        self.cancel_btn.pack(after=self.save_btn, pady=5)

    def clear_form(self):
        self.editing_mode = False

        self.mode_label.config(
            text="🆕 NEW REGISTRATION",
            bg="#e8f5e9",
            fg="#2e7d32"
        )

        self.save_btn.config(
            text="➕ REGISTER CARD",
            bg="#4CAF50"
        )

        self.cancel_btn.pack_forget()

        self.edit_btn.pack(pady=5)

        self.emp_id_entry.config(state="normal")
        self.rfid_entry.config(state="normal")

        self.emp_id_entry.delete(0, tk.END)
        self.rfid_entry.delete(0, tk.END)

        self.emp_id_entry.focus_set()

    def handle_save(self):
        eid = self.emp_id_entry.get().strip()
        uid = self.rfid_entry.get().strip()

        if not eid or not uid:
            messagebox.showwarning("Input Error", "ID and RFID are required.")
            return

        try:
            with db_connect() as conn:
                with conn.cursor() as cur:
                    # 1. Check if Teacher exists in main users table
                    cur.execute("SELECT username FROM users WHERE employee_id = %s AND role = 'Teacher'", (eid,))
                    teacher_exists = cur.fetchone()
                    
                    if not teacher_exists:
                        messagebox.showerror("Error", f"Employee ID {eid} is not a registered Teacher.")
                        return

                    # 2. Duplicate check
                    cur.execute("SELECT employee_id FROM teacher_rfid_registration WHERE rfid_uid = %s AND employee_id != %s", (uid, eid))
                    if cur.fetchone():
                        messagebox.showerror("Duplicate RFID", "This card is already assigned to another teacher.")
                        return

                    # 3. Save
                    cur.execute("""
                        INSERT INTO teacher_rfid_registration (employee_id, rfid_uid, status) 
                        VALUES (%s, %s, 'Active') 
                        ON DUPLICATE KEY UPDATE rfid_uid = VALUES(rfid_uid)
                    """, (eid, uid))
                    conn.commit()

            messagebox.showinfo("Success", "Master access granted.")
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
        eid = self.emp_id_entry.get().strip()
        if not eid:
            return

        confirm = messagebox.askyesno(
            "Confirm Delete",
            "Are you sure you want to delete this record?"
        )

        if not confirm:
            return

        try:
            with db_connect() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "DELETE FROM teacher_rfid_registration WHERE employee_id = %s",
                        (eid,)
                    )
                    conn.commit()

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
                    cur.execute("UPDATE teacher_rfid_registration SET status = %s WHERE employee_id = %s", (new_status, eid))
                    conn.commit()
            self.refresh_list()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    
    def handle_rfid_tap(self, uid):
        # Only fill if RFID entry is focused
        focused = self.focus_get()

        if focused == self.rfid_entry:
            self.rfid_entry.delete(0, tk.END)
            self.rfid_entry.insert(0, uid)
            print("Override RFID filled:", uid)

    def validate_rfid(self, value):
        # Reject spaces
        if " " in value:
            return False
        return True