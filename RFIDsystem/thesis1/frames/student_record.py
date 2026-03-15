import tkinter as tk
from tkinter import messagebox, filedialog, ttk
from PIL import ImageTk, Image
import os
import sys
import io 

# ================= PATH SETUP =================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from utils.database import db_connect

class StudentRecord(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#b2e5ed")
        self.controller = controller
        self.photo_path = None

        # ================= PAGINATION & SEARCH STATE =================
        self.page_size = 100
        self.current_page = 1
        self.total_students = 0
        self.search_results = [] 
        self.search_page = 1     

        # ================= VALIDATORS =================
        self.num_validate = self.register(self.only_numbers)
        self.contact_validate = self.register(self.contact_limit)

        # ================= HEADER =================
        header = tk.Frame(self, height=70, bg="#0047AB")
        header.pack(fill="x")
        tk.Label(header, text="STUDENT INFORMATION", font=("Arial", 20, "bold"),
                 bg="#0047AB", fg="white").place(x=30, y=18)

        # ================= LEFT PANEL =================
        self.left_box = tk.Frame(self, width=480, height=520, bg="white", bd=2, relief="groove")
        self.left_box.place(x=20, y=90)
        self.left_box.pack_propagate(False)

        # ================= PHOTO SECTION =================
        self.photo_frame = tk.Frame(self.left_box, width=160, height=160, bg="#E0E0E0", bd=2, relief="ridge")
        self.photo_frame.place(x=20, y=20)
        self.photo_frame.pack_propagate(False)

        self.photo_label = tk.Label(self.photo_frame, bg="#E0E0E0")
        self.photo_label.pack(fill="both", expand=True)

        self.upload_btn = tk.Button(self.left_box, text="Upload Photo", width=14, command=self.upload_photo)
        self.upload_btn.place(x=210, y=80)
        
        self.remove_photo_btn = tk.Button(self.left_box, text="Remove Photo", width=14, fg="red", command=self.remove_photo)
        self.remove_photo_btn.place(x=210, y=115) 

        # ================= VARIABLES =================
        self.student_name_var = tk.StringVar()
        self.grade_var = tk.StringVar()
        self.student_id_var = tk.StringVar()
        self.guardian_name_var = tk.StringVar()
        self.guardian_contact_var = tk.StringVar()
        
        self.guardian_contact_var.trace_add("write", self.format_contact)

        self.edit_mode = False
        self.original_student_id = None

        self.edit_label = tk.Label(self.left_box, text="VIEW MODE", font=("Arial", 10, "bold"),
                                   fg="gray", bg="white")
        self.edit_label.place(x=280, y=10)

        # ================= FORM FIELDS =================
        fields = [
            ("Full Name:", self.student_name_var),
            ("Student ID:", self.student_id_var),
            ("Guardian Name:", self.guardian_name_var),
            ("Guardian Contact:", self.guardian_contact_var),
        ]

        self.entries = {}
        y_start = 200
        for i, (label, var) in enumerate(fields):
            tk.Label(self.left_box, text=label, bg="white", font=("Arial", 11)).place(x=20, y=y_start + i * 40)

            if label == "Grade:":
                grade_options = ["K1", "K2", "1", "2", "3", "4", "5", "6"]
                entry = ttk.Spinbox(self.left_box, values=grade_options, textvariable=var, 
                                    width=28, state="readonly")
            elif label == "Student ID:":
                entry = tk.Entry(self.left_box, textvariable=var, width=30, font=("Arial", 11),
                                 validate="key", validatecommand=(self.num_validate, "%P"))
                self.student_id_entry = entry
            elif label == "Guardian Contact:":
                entry = tk.Entry(self.left_box, textvariable=var, width=30, font=("Arial", 11),
                                 validate="key", validatecommand=(self.contact_validate, "%P"))
            else:
                entry = tk.Entry(self.left_box, textvariable=var, width=30, font=("Arial", 11))

            entry.place(x=150, y=y_start + i * 40)
            self.entries[label] = entry

        # ================= ACTION BUTTONS =================
        btn_frame = tk.Frame(self.left_box, bg="white")
        btn_frame.place(x=15, y=470)

        self.add_btn = tk.Button(btn_frame, text="ADD", width=9, bg="#4CAF50", fg="white",
                                 font=("Arial", 9, "bold"), command=self.add_student)
        self.add_btn.grid(row=0, column=0, padx=2)

        self.edit_btn = tk.Button(btn_frame, text="EDIT", width=9, bg="#2196F3", fg="white",
                                  font=("Arial", 9, "bold"), command=self.enable_edit_mode)
        self.edit_btn.grid(row=0, column=1, padx=2)

        self.update_btn = tk.Button(btn_frame, text="UPDATE", width=9, bg="#FF9800", fg="white",
                                    font=("Arial", 9, "bold"), command=self.edit_student, state="disabled")
        self.update_btn.grid(row=0, column=2, padx=2)

        self.delete_btn = tk.Button(btn_frame, text="DELETE", width=9, bg="#F44336", fg="white",
                                    font=("Arial", 9, "bold"), command=self.delete_student)
        self.delete_btn.grid(row=0, column=3, padx=2)

        # ================= RIGHT PANEL =================
        self.right_panel = tk.Frame(self, width=540, height=520, bg="white", bd=2, relief="groove")
        self.right_panel.place(x=520, y=90)
        self.right_panel.pack_propagate(False)

        tk.Label(self.right_panel, text="Search Student (Name or  Student ID )", font=("Arial", 14, "bold"), bg="white").place(x=20, y=15)

        self.search_var = tk.StringVar()
        tk.Entry(self.right_panel, textvariable=self.search_var, width=25, font=("Arial", 11)).place(x=20, y=50)

        tk.Button(self.right_panel, text="Search", command=self.search_student).place(x=260, y=47)
        tk.Button(self.right_panel, text="Clear", command=self.clear_search).place(x=320, y=47)

        self.count_var = tk.StringVar()
        tk.Label(self.right_panel, textvariable=self.count_var, font=("Arial", 11, "bold"),
                 fg="#0047AB", bg="white").place(x=20, y=85)

        self.student_table = ttk.Treeview(
            self.right_panel,
            columns=("Student_id", "Student_name", "Guardian_name"),
            show="headings",
            height=15
        )

        for col, txt, w in [
            ("Student_id", "Student ID", 120),
            ("Student_name", "Full Name", 200),
            ("Guardian_name", "Guardian Name", 180)
        ]:
            self.student_table.heading(col, text=txt)
            self.student_table.column(col, width=w)

        self.student_table.place(x=20, y=120, width=500)
        self.student_table.bind("<<TreeviewSelect>>", self.on_table_select)

        nav = tk.Frame(self.right_panel, bg="white")
        nav.place(x=200, y=470)
        tk.Button(nav, text="◀ Prev", command=self.prev_page).grid(row=0, column=0, padx=5)
        tk.Button(nav, text="Next ▶", command=self.next_page).grid(row=0, column=1, padx=5)

        self.reset_ui_state()
        self.load_data()

    # ================= LOGIC METHODS =================
    def display_photo(self, data):
        """Handles displaying photo from either a file path or database binary data."""
        try:
            if data:
                # Check if data is binary (from DB) or a file path (from Upload)
                if isinstance(data, (bytes, bytearray)):
                    stream = io.BytesIO(data)
                    img = Image.open(stream)
                else:
                    # It's a file path string
                    img = Image.open(data)
                
                img = img.resize((160, 160), Image.Resampling.LANCZOS)
                self.photo = ImageTk.PhotoImage(img)
                self.photo_label.config(image=self.photo, text="")
                self.photo_label.image = self.photo # Keep reference
            else:
                self.photo_label.config(image="", text="NO PHOTO", font=("Arial", 10, "bold"))
        except Exception as e:
            print(f"Photo error: {e}")
            self.photo_label.config(image="", text="Error Image")

    def upload_photo(self):
        path = filedialog.askopenfilename(filetypes=[("Image Files", "*.jpg *.jpeg *.png")])
        if path:
            self.photo_path = path
            self.display_photo(path) # Updated call

    def remove_photo(self):
        self.photo_path = None
        self.display_photo(None) # Updated call


    def only_numbers(self, v): return v.isdigit() or v == ""
    def contact_limit(self, v): return (v.isdigit() and len(v) <= 11) or v == ""

    def format_contact(self, *_):
        val = self.guardian_contact_var.get()
        if val.startswith("9") and len(val) == 10: self.guardian_contact_var.set("0" + val)

    def set_fields_state(self, state):
        for label, entry in self.entries.items():
            if label == "Grade:": entry.config(state="readonly" if state == "disabled" else "normal")
            else: entry.config(state=state)
        self.upload_btn.config(state=state)
        self.remove_photo_btn.config(state=state)

    def reset_ui_state(self):
        self.edit_mode = False
        self.set_fields_state("disabled")
        self.student_id_entry.config(state="disabled")
        self.add_btn.config(text="ADD", state="normal", bg="#4CAF50")
        self.edit_btn.config(state="normal")
        self.delete_btn.config(text="DELETE", bg="#F44336")
        self.update_btn.config(state="disabled")
        self.edit_label.config(text="VIEW MODE", fg="gray", bg="white")
        self.clear_fields()

    def clear_fields(self):
        for var in (self.student_name_var, self.student_id_var, self.grade_var,
                    self.guardian_name_var, self.guardian_contact_var,):
            var.set("")
        self.display_photo(None)
        self.photo_path = None

    def load_data(self):
        self.student_table.delete(*self.student_table.get_children())
        offset = (self.current_page - 1) * self.page_size
        try:
            with db_connect() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT COUNT(*) FROM student")
                    self.total_students = cursor.fetchone()[0]
                    cursor.execute("SELECT Student_id, Student_name, Guardian_name FROM student LIMIT %s OFFSET %s", (self.page_size, offset))
                    for row in cursor.fetchall(): self.student_table.insert("", "end", values=row)
            total_p = max(1, (self.total_students + self.page_size - 1) // self.page_size)
            self.count_var.set(f"Students: {self.total_students} | Page {self.current_page}/{total_p}")
        except Exception as e:
            print(f"Load error: {e}")

    def search_student(self):
        keyword = self.search_var.get().strip()
        if not keyword: 
            messagebox.showinfo("Search", "Please enter a keyword.") 
            return self.clear_search()
        try:
            with db_connect() as conn:
                with conn.cursor() as cursor:
                    query = "SELECT Student_id, Student_name, Guardian_name FROM student WHERE Student_name LIKE %s OR Student_id LIKE %s"
                    cursor.execute(query, (f"%{keyword}%", f"%{keyword}%"))
                    self.search_results = cursor.fetchall()
            
            if not self.search_results:
                messagebox.showinfo("Search", "No results found.")
                return self.clear_search()
            
            self.search_page = 1
            self.update_search_table()
        except Exception as e:
            print(f"Search error: {e}")

    def update_search_table(self):
        self.student_table.delete(*self.student_table.get_children())
        start = (self.search_page - 1) * self.page_size
        end = start + self.page_size
        for row in self.search_results[start:end]: self.student_table.insert("", "end", values=row)
        total_p = max(1, (len(self.search_results) + self.page_size - 1) // self.page_size)
        self.count_var.set(f"Matches: {len(self.search_results)} | Page {self.search_page}/{total_p}")

    def clear_search(self):
        self.search_var.set("")
        self.search_results = []
        self.current_page = 1
        self.load_data()
        self.clear_fields()

    def next_page(self):
        if self.search_results:
            if self.search_page * self.page_size < len(self.search_results): 
                self.search_page += 1
                self.update_search_table()
        else:
            # Check if there is a next page based on total_students
            total_p = (self.total_students + self.page_size - 1) // self.page_size
            if self.current_page < total_p: 
                self.current_page += 1
                self.load_data()

    def prev_page(self):
        if self.search_results:
            if self.search_page > 1: 
                self.search_page -= 1
                self.update_search_table()
        else:
            if self.current_page > 1: 
                self.current_page -= 1
                self.load_data()

    def on_table_select(self, _):
        if self.edit_mode or self.add_btn["text"] == "SAVE": return
        sel = self.student_table.selection()
        if not sel: return
        sid = self.student_table.item(sel[0], "values")[0]
        try:
            with db_connect() as conn:
                with conn.cursor(dictionary=True) as cursor:
                    cursor.execute("SELECT * FROM student WHERE Student_id=%s", (sid,))
                    student = cursor.fetchone()
            if student:
                self.student_id_var.set(student["Student_id"])
                self.student_name_var.set(student["Student_name"])
                self.guardian_name_var.set(student["Guardian_name"])
                self.guardian_contact_var.set(student["Guardian_contact"])
                
                # Fetching the BLOB from the photo_path column
                self.photo_path = student["photo_path"] 
                self.display_photo(self.photo_path)
        except Exception as e:
            print(f"Select error: {e}")

    def add_student(self):
        if self.add_btn["text"] == "ADD":
            self.clear_fields()
            self.set_fields_state("normal")
            self.student_id_entry.config(state="normal")
            self.add_btn.config(text="SAVE", bg="#2E7D32")
            self.edit_btn.config(state="disabled")
            self.delete_btn.config(text="CANCEL", bg="#757575")
            self.edit_label.config(text="ADD MODE", fg="white", bg="#4CAF50")
            return

        error = self.validate()
        if error: 
            return messagebox.showerror("Validation Error", error)
    
        sid = self.student_id_var.get()
        if self.student_id_exists(sid): 
            return messagebox.showerror("Error", f"Student ID {sid} already exists.")

        binary_photo = None
        if self.photo_path and isinstance(self.photo_path, str):
            img = Image.open(self.photo_path).convert("RGB")
            buf = io.BytesIO()
            img.save(buf, format='JPEG')
            binary_photo = buf.getvalue()

        try:
            with db_connect() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                    INSERT INTO student 
                    (Student_name, Student_id, Guardian_name, Guardian_contact, photo_path) 
                    VALUES (%s,%s,%s,%s,%s)""",
                    (self.student_name_var.get(), sid,
                    self.guardian_name_var.get(), self.guardian_contact_var.get(),
                    binary_photo))
                    conn.commit()
            messagebox.showinfo("Success", "Student record added successfully!")
            self.reset_ui_state()
            self.load_data()
        except Exception as e:
            messagebox.showerror("Database Error", f"Could not save: {str(e)}")

    def enable_edit_mode(self):
        if not self.student_id_var.get(): 
            return messagebox.showwarning("Warning", "Please select a student first.")
        else: 
            ask= messagebox.askyesno("Confirm", "Are you sure you want to edit this student?")
            if not ask: 
                return
        self.edit_mode = True
        self.original_student_id = self.student_id_var.get()
        self.set_fields_state("normal")
        self.student_id_entry.config(state="normal")
        self.update_btn.config(state="normal")
        self.edit_btn.config(state="disabled")
        self.delete_btn.config(text="CANCEL", bg="#757575")
        self.edit_label.config(text="EDIT MODE", bg="red", fg="white")

    def edit_student(self):
        error = self.validate()
        if error: return messagebox.showerror("Error", error)
        
        new_sid = self.student_id_var.get()
        if new_sid != self.original_student_id and self.student_id_exists(new_sid):
            return messagebox.showerror("Error", f"Student ID {new_sid} is taken.")

        binary_photo = self.photo_path if isinstance(self.photo_path, bytes) else None
        if self.photo_path and isinstance(self.photo_path, str):
            img = Image.open(self.photo_path).convert("RGB")
            buf = io.BytesIO()
            img.save(buf, format='JPEG')
            binary_photo = buf.getvalue()

        try:
            with db_connect() as conn:
                with conn.cursor() as cur:
                    cur.execute("""UPDATE student SET Student_name=%s,
                                   Guardian_name=%s, Guardian_contact=%s, Student_id=%s, 
                                   photo_path=%s WHERE Student_id=%s""",
                                (self.student_name_var.get(), self.guardian_name_var.get(), self.guardian_contact_var.get(), 
                                 new_sid, binary_photo, self.original_student_id))
                    conn.commit()
            messagebox.showinfo("Success", "Record updated!")
            self.reset_ui_state()
            self.load_data()
        except Exception as e:
            messagebox.showerror("Database Error", f"Update failed: {e}")

    def delete_student(self):
        if self.delete_btn["text"] == "CANCEL": 
            self.reset_ui_state()
            return
        
        sid = self.student_id_var.get()
        if not sid: return messagebox.showwarning("Warning", "Select a student.")

        if messagebox.askyesno("Confirm", f"Delete Student ID: {sid}?\n\nNote: This student will disappear from the master list, but their name will remain in the Teacher's Class History."):
            try:
                with db_connect() as conn:
                    with conn.cursor() as cur:
                        # WE REMOVED THE DELETE FROM CLASSROOM LINE HERE.
                        # This allows the classroom table to keep the student's name/data.

                        # Just delete from the main student record
                        cur.execute("DELETE FROM student WHERE Student_id=%s", (sid,))
                        conn.commit()
                
                messagebox.showinfo("Success", "Master record deleted. Classroom history preserved.")
                
                if len(self.student_table.get_children()) <= 1 and self.current_page > 1:
                    self.current_page -= 1
                    
                self.reset_ui_state()
                self.load_data()
            except Exception as e:
                # If you get a "Foreign Key Constraint" error here, see the SQL fix below.
                messagebox.showerror("Error", f"Delete failed: {e}")

    def validate(self):
        name = self.student_name_var.get().strip()
        sid = self.student_id_var.get().strip()
        grade = self.grade_var.get().strip()
        if not name: return "Name is required."
        if not sid.isdigit(): return "Student ID must be numeric."
        return None

    def student_id_exists(self, sid):
        try:
            with db_connect() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT Student_id FROM student WHERE Student_id=%s", (sid,))
                    return cur.fetchone() is not None
        except: return False