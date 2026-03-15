import tkinter as tk
from tkinter import messagebox, ttk
import os, sys

# Ensure utility imports work
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

from utils.database import db_connect

class AdminOverrideFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#f0e5ed")
        self.controller = controller
        self.mode = None  # "add" or "edit"

        # --- Header ---
        header = tk.Frame(self, bg="#6A1B9A", height=60)
        header.pack(fill="x")
        tk.Label(header, text="ADMIN MASTER RFID MANAGEMENT", font=("Arial", 18, "bold"),
                 bg="#6A1B9A", fg="white").pack(pady=10)

        # --- Main Layout ---
        main_container = tk.Frame(self, bg="#f0e5ed")
        main_container.pack(fill="both", expand=True, padx=20, pady=20)

        # --- LEFT: Form ---
        self.form_container = tk.Frame(main_container, bg="white", padx=20, pady=20,
                                        highlightthickness=2, highlightbackground="#CCCCCC")
        self.form_container.pack(side="left", fill="y", padx=(0, 20))

        self.mode_label = tk.Label(self.form_container, text="IDLE: SELECT ACTION",
                                    font=("Arial", 10, "bold"), bg="#f5f5f5", fg="#757575", pady=5)
        self.mode_label.pack(fill="x", pady=(0, 15))

        tk.Label(self.form_container, text="Admin Employee ID:", bg="white", font=("Arial", 9, "bold")).pack(anchor="w")
        self.emp_id_entry = tk.Entry(self.form_container, font=("Arial", 11), width=25, bd=1, relief="solid")
        self.emp_id_entry.pack(pady=(5, 15), ipady=3)

        tk.Label(self.form_container, text="RFID UID (Tap Card):", bg="white",
                 font=("Arial", 9, "bold"), fg="#6A1B9A").pack(anchor="w")
        self.rfid_entry = tk.Entry(self.form_container, font=("Arial", 11), width=25, bd=1,
                                   relief="solid", justify="center")
        self.rfid_entry.pack(pady=(5, 10), ipady=3)
        self.rfid_entry.bind("<Return>", lambda e: self.handle_save())

        # Action Buttons
        self.add_btn = tk.Button(self.form_container, text="➕ ADD NEW", command=self.start_add,
                                 bg="#4CAF50", fg="white", font=("Arial", 9, "bold"), width=20, pady=6)
        self.add_btn.pack(pady=3)

        self.edit_btn = tk.Button(self.form_container, text="✏ EDIT SELECTED", command=self.start_edit,
                                  bg="#FF9800", fg="white", font=("Arial", 9, "bold"), width=20, pady=6)
        self.edit_btn.pack(pady=3)

        self.save_btn = tk.Button(self.form_container, text="💾 SAVE CHANGES", command=self.handle_save,
                                  bg="#2196F3", fg="white", font=("Arial", 9, "bold"), width=20, pady=6)
        self.save_btn.pack(pady=3)

        self.del_btn = tk.Button(self.form_container, text="🗑 DELETE", command=self.handle_delete,
                                 bg="#f44336", fg="white", font=("Arial", 9, "bold"), width=20, pady=6)
        self.del_btn.pack(pady=3)

        self.cancel_btn = tk.Button(self.form_container, text="✖ CANCEL", command=self.clear_form,
                                    bg="#757575", fg="white", font=("Arial", 9, "bold"), width=20, pady=6)

        # --- RIGHT: List ---
        list_container = tk.Frame(main_container, bg="white", padx=10, pady=10,
                                  highlightthickness=1, highlightbackground="#CCCCCC")
        list_container.pack(side="right", fill="both", expand=True)

        list_header = tk.Frame(list_container, bg="white")
        list_header.pack(fill="x", pady=(0, 10))
        tk.Label(list_header, text="Registered Admin Overrides", font=("Arial", 11, "bold"), bg="white").pack(side="left")

        tk.Button(list_header, text="✅ ACTIVATE", bg="#2196F3", fg="white", font=("Arial", 8, "bold"),
                  command=lambda: self.toggle_status("Active")).pack(side="right", padx=2)
        tk.Button(list_header, text="🚫 DEACTIVATE", bg="#FF9800", fg="white", font=("Arial", 8, "bold"),
                  command=lambda: self.toggle_status("Deactivated")).pack(side="right", padx=2)

        self.tree = ttk.Treeview(list_container, columns=("EID", "Name", "UID", "Status"), show="headings", height=15)
        self.tree.heading("EID", text="Emp ID")
        self.tree.heading("Name", text="Admin Name")
        self.tree.heading("UID", text="RFID UID")
        self.tree.heading("Status", text="Status")
        self.tree.column("EID", width=70, anchor="center")
        self.tree.column("Status", width=100, anchor="center")
        self.tree.pack(fill="both", expand=True)

        self.refresh_list()
        self.clear_form()

    # ---------------- UI STATE CONTROL ----------------
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
        self.mode_label.config(text="➕ ADDING NEW ADMIN", bg="#f3e5f5", fg="#6A1B9A")
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

        self.mode_label.config(text=f"✏️ EDITING: {values[1]}", bg="#fce4ec", fg="#ad1457")
        self.rfid_entry.focus_set()

    def clear_form(self):
        self.mode = None
        self.emp_id_entry.config(state="normal")
        self.emp_id_entry.delete(0, tk.END)
        self.rfid_entry.config(state="normal")
        self.rfid_entry.delete(0, tk.END)
        self.set_ui_state("idle")

    def handle_save(self):
        eid = self.emp_id_entry.get().strip()
        uid = self.rfid_entry.get().strip()
        if not eid or not uid:
            messagebox.showwarning("Input Error", "Admin ID and RFID UID are required.")
            return

        try:
            with db_connect() as conn:
                with conn.cursor() as cur:
                    # Validate admin exists
                    cur.execute("SELECT username FROM users WHERE employee_id=%s AND role='Admin'", (eid,))
                    if not cur.fetchone():
                        messagebox.showerror("Error", f"ID {eid} is not a registered Admin.")
                        return

                    if self.mode == "add":
                        # Check existing registration
                        cur.execute("SELECT employee_id FROM admin_rfid_registration WHERE employee_id=%s", (eid,))
                        if cur.fetchone():
                            messagebox.showerror("Error", "This Admin is already registered. Use Edit instead.")
                            return
                        cur.execute("INSERT INTO admin_rfid_registration (employee_id, rfid_uid, status) VALUES (%s, %s, 'Active')", (eid, uid))
                    else:  # edit
                        cur.execute("UPDATE admin_rfid_registration SET rfid_uid=%s WHERE employee_id=%s", (uid, eid))
                    conn.commit()

            messagebox.showinfo("Success", "Database updated successfully.")
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
                        SELECT a.employee_id, u.username, a.rfid_uid, a.status
                        FROM admin_rfid_registration a
                        JOIN users u ON a.employee_id = u.employee_id
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
            messagebox.showwarning("Select Record", "Please select a record first.")
            return
        eid = self.tree.item(selected, "values")[0]
        if messagebox.askyesno("Confirm Delete", "Delete this Admin RFID?"):
            try:
                with db_connect() as conn:
                    with conn.cursor() as cur:
                        cur.execute("DELETE FROM admin_rfid_registration WHERE employee_id=%s", (eid,))
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
                    cur.execute("UPDATE admin_rfid_registration SET status=%s WHERE employee_id=%s", (new_status, eid))
                    conn.commit()
            self.refresh_list()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def handle_rfid_tap(self, uid):
      # Only paste UID if the RFID input box is currently selected
      focused = self.focus_get()

      if focused == self.rfid_entry:
          self.rfid_entry.delete(0, tk.END)
          self.rfid_entry.insert(0, uid)

          print("Admin Override RFID filled:", uid)