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

class TeacherRecord(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#b2e5ed")
        self.controller = controller

        # ================= STATE VARIABLES =================
        self.photo_path = None  
        self.photo = None 
        self.edit_mode = False
        self.current_teacher_id = None

        # ================= PAGINATION & SEARCH =================
        self.page_size = 50
        self.current_page = 1
        self.total_teachers = 0
        self.search_results = []
        self.search_page = 1

        # ================= HEADER =================
        header = tk.Frame(self, height=70, bg="#0047AB")
        header.pack(fill="x")
        tk.Label(header, text="TEACHER INFORMATION",
                 font=("Arial", 20, "bold"), bg="#0047AB", fg="white").place(x=30, y=18)

        # ================= LEFT PANEL (FORM) =================
        self.left_box = tk.Frame(self, width=430, height=480, bg="white", bd=2, relief="groove")
        self.left_box.place(x=40, y=90)
        self.left_box.pack_propagate(False)

        # Photo UI
        self.photo_frame = tk.Frame(self.left_box, width=160, height=160, bg="#E0E0E0", bd=2, relief="ridge")
        self.photo_frame.place(x=20, y=20)
        self.photo_frame.pack_propagate(False)

        self.photo_label = tk.Label(self.photo_frame, bg="#E0E0E0")
        self.photo_label.pack(fill="both", expand=True)

        self.upload_btn = tk.Button(self.left_box, text="Upload Photo", width=14, command=self.upload_photo)
        self.upload_btn.place(x=210, y=70)

        self.remove_btn = tk.Button(self.left_box, text="Remove Photo", width=14, fg="red", command=self.remove_photo_action)
        self.remove_btn.place(x=210, y=105)

        self.edit_label = tk.Label(self.left_box, text="VIEW MODE", font=("Arial", 10, "bold"), fg="gray", bg="white")
        self.edit_label.place(x=280, y=10)

        # Form Variables
        self.teacher_name_var = tk.StringVar()
        self.department_var = tk.StringVar()
        self.employee_id_var = tk.StringVar()

        self.num_validate = self.register(lambda v: v.isdigit() or v == "")

        tk.Label(self.left_box, text="Teacher Name:", bg="white", font=("Arial", 11)).place(x=20, y=200)
        self.name_entry = tk.Entry(self.left_box, textvariable=self.teacher_name_var, width=30, font=("Arial", 11))
        self.name_entry.place(x=150, y=200)

        tk.Label(self.left_box, text="Department:", bg="white", font=("Arial", 11)).place(x=20, y=240)

        self.department_dropdown = ttk.Combobox(
            self.left_box,
            textvariable=self.department_var,
            values=["Pre-School", "Grade School"],
            state="readonly",
            width=27
        )
        self.department_dropdown.place(x=150, y=240)


        tk.Label(self.left_box, text="Employee ID:", bg="white", font=("Arial", 11)).place(x=20, y=280)

        self.employee_id_entry = tk.Entry(
            self.left_box,
            textvariable=self.employee_id_var,
            width=30,
            font=("Arial", 11),
            validate="key",
            validatecommand=(self.num_validate, "%P")
        )
        self.employee_id_entry.place(x=150, y=280)

        # Action Buttons
        btn_frame = tk.Frame(self.left_box, bg="white")
        btn_frame.place(x=15, y=320)

        self.add_btn = tk.Button(btn_frame, text="ADD", width=9, bg="#4CAF50", fg="white", 
                                 font=("Arial", 9, "bold"), command=self.add_teacher)
        self.add_btn.grid(row=0, column=0, padx=2)

        self.edit_btn = tk.Button(btn_frame, text="EDIT", width=9, bg="#2196F3", fg="white", 
                                  font=("Arial", 9, "bold"), command=self.enable_edit_mode)
        self.edit_btn.grid(row=0, column=1, padx=2)

        self.update_btn = tk.Button(btn_frame, text="UPDATE", width=9, bg="#FF9800", fg="white", 
                                    font=("Arial", 9, "bold"), command=self.update_teacher_db, state="disabled")
        self.update_btn.grid(row=0, column=2, padx=2)

        self.delete_btn = tk.Button(btn_frame, text="DELETE", width=9, bg="#F44336", fg="white", 
                                    font=("Arial", 9, "bold"), command=self.delete_teacher)
        self.delete_btn.grid(row=0, column=3, padx=2)

        # ================= RIGHT PANEL (TABLE & SEARCH) =================
        self.right_panel = tk.Frame(self, width=500, height=480, bg="white", bd=2, relief="groove")
        self.right_panel.place(x=520, y=90)
        self.right_panel.pack_propagate(False)

        tk.Label(self.right_panel, text="Search Teacher (NAME/DEPARTMENT)", font=("Arial", 14, "bold"), bg="white").place(x=20, y=15)

        self.search_var = tk.StringVar()
        tk.Entry(self.right_panel, textvariable=self.search_var, width=25, font=("Arial", 11)).place(x=20, y=50)
        self.search_var.trace_add("write", lambda *args: self.live_search())
        tk.Button(self.right_panel, text="Search", command=self.search_teacher).place(x=260, y=47)
        
        # Link to clear_search for complete UI reset
        tk.Button(self.right_panel, text="Clear", command=self.clear_search).place(x=320, y=47)

        self.teacher_count_var = tk.StringVar(value="Total Records: 0 | Page 1/1")
        tk.Label(self.right_panel, textvariable=self.teacher_count_var, font=("Arial", 11, "bold"), fg="#0047AB", bg="white").place(x=20, y=85)

        # Table
        columns = ("teacher_id", "name", "department")
        self.teacher_table = ttk.Treeview(self.right_panel, columns=columns, show="headings", height=12)
        self.teacher_table.heading("teacher_id", text="ID")
        self.teacher_table.heading("name", text="Teacher Name")
        self.teacher_table.heading("department", text="Department")
        self.teacher_table.column("teacher_id", width=50)
        self.teacher_table.column("name", width=240)
        self.teacher_table.column("department", width=120)
        self.teacher_table.place(x=20, y=120, width=450)
        self.teacher_table.bind("<<TreeviewSelect>>", self.on_select)

        # Pagination
        nav = tk.Frame(self.right_panel, bg="white")
        nav.place(x=160, y=420)
        tk.Button(nav, text="◀ Prev", command=self.prev_page).grid(row=0, column=0, padx=5)
        tk.Button(nav, text="Next ▶", command=self.next_page).grid(row=0, column=1, padx=5)

        self.reset_ui_state()
        self.load_teachers()

    # ================= HELPERS & UI CONTROL =================
    def display_photo(self, data):
        try:
            if data:
                if isinstance(data, bytes):
                    stream = io.BytesIO(data)
                    img = Image.open(stream).resize((160, 160))
                else:
                    img = Image.open(data).resize((160, 160))
                
                self.photo = ImageTk.PhotoImage(img)
                self.photo_label.config(image=self.photo, text="")
                self.photo_label.image = self.photo
            else:
                self.photo_label.config(image="", text="NO PHOTO\nAVAILABLE", 
                                        font=("Arial", 10, "bold"), fg="#666666")
                self.photo = None
        except Exception as e:
            self.photo_label.config(image="", text="Error Image")

    def upload_photo(self):
        path = filedialog.askopenfilename(filetypes=[("Image Files", "*.jpg *.png *.jpeg")])
        if path:
            self.photo_path = path
            self.display_photo(path)

    def remove_photo_action(self):
        if self.add_btn["text"] == "SAVE" or self.edit_mode:
            if messagebox.askyesno("Confirm", "Remove photo from this record?"):
                self.photo_path = None
                self.display_photo(None)
        else:
            messagebox.showwarning("Warning", "Enable Edit Mode or Add Mode to change photos.")

    def set_fields_state(self, state):
        self.name_entry.config(state=state)
        self.department_dropdown.config(state="readonly" if state=="normal" else "disabled")
        self.employee_id_entry.config(state=state)
        self.upload_btn.config(state=state)
        self.remove_btn.config(state=state)

    def reset_ui_state(self):
        self.edit_mode = False
        self.current_teacher_id = None
        self.set_fields_state("disabled")
        self.add_btn.config(text="ADD", state="normal", bg="#4CAF50")
        self.edit_btn.config(state="normal", bg="#2196F3")
        self.delete_btn.config(text="DELETE", bg="#F44336")
        self.update_btn.config(state="disabled")
        self.edit_label.config(text="VIEW MODE", fg="gray", bg="white")
        self.clear_fields()

    def clear_fields(self):
        self.teacher_name_var.set("")
        self.department_var.set("")
        self.employee_id_var.set("")
        self.display_photo(None)
        self.photo_path = None
        self.teacher_table.selection_remove(self.teacher_table.selection())

    def validate_fields(self):
        if not self.teacher_name_var.get().strip():
            return "Teacher Name is required"
        if not self.department_var.get().strip():
            return "Department is required"
        if not self.employee_id_var.get().strip():
            return "Employee ID is required"
        return None

    # ================= CRUD LOGIC =================
    def add_teacher(self):
        if self.add_btn["text"] == "ADD":
            self.reset_ui_state()
            self.set_fields_state("normal")
            
            
            self.add_btn.config(text="SAVE", bg="#2E7D32")
            self.edit_btn.config(state="disabled")
            self.edit_label.config(text="ADD MODE", fg="white", bg="green")
            self.delete_btn.config(text="CANCEL", bg="#757575")
            return

        error = self.validate_fields()
        if error: return messagebox.showerror("Error", error)

        try:
            binary_photo = None
            if self.photo_path and os.path.exists(self.photo_path):
                img = Image.open(self.photo_path).convert("RGB")
                img_byte_arr = io.BytesIO()
                img.save(img_byte_arr, format='JPEG')
                binary_photo = img_byte_arr.getvalue()

            with db_connect() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                                    "INSERT INTO teacher (teacher_name, department, employee_id, photo_path) VALUES (%s, %s, %s, %s)",
                                   (self.teacher_name_var.get().strip(),
                                    self.department_var.get().strip(),
                                    self.employee_id_var.get().strip(),
                                    binary_photo))
                    conn.commit()
            
            messagebox.showinfo("Success", "Teacher added successfully")
            self.reset_ui_state()
            self.load_teachers()
        except Exception as e:
            messagebox.showerror("Database Error", f"Error saving teacher: {e}")

    def update_teacher_db(self):
        error = self.validate_fields()
        if error: return messagebox.showerror("Error", error)

        try:
            sql_parts = ["teacher_name=%s", "department=%s", "employee_id=%s"]
            params = [
                self.teacher_name_var.get().strip(),
                self.department_var.get().strip(),
                self.employee_id_var.get().strip()
            ]

            if self.photo_path is None:
                sql_parts.append("photo_path=NULL")
            elif not isinstance(self.photo_path, bytes):
                img = Image.open(self.photo_path).convert("RGB")
                img_byte_arr = io.BytesIO()
                img.save(img_byte_arr, format='JPEG')
                sql_parts.append("photo_path=%s")
                params.append(img_byte_arr.getvalue())

            params.append(self.current_teacher_id)
            query = f"UPDATE teacher SET {', '.join(sql_parts)} WHERE teacher_id=%s"

            with db_connect() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, params)
                    conn.commit()
            messagebox.showinfo("Success", "Teacher record updated")
            self.reset_ui_state()
            self.load_teachers()
        except Exception as e:
            messagebox.showerror("Error", f"Update failed: {e}")

    def on_select(self, _):
        if self.edit_mode or self.add_btn["text"] == "SAVE": return
        sel = self.teacher_table.focus()
        if not sel: return
        
        data = self.teacher_table.item(sel, "values")
        self.current_teacher_id = data[0]
        self.teacher_name_var.set(data[1])
        self.department_var.set(data[2])

        try:
            with db_connect() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        "SELECT photo_path, employee_id FROM teacher WHERE teacher_id=%s",
                        (self.current_teacher_id,)
                    )

                    row = cursor.fetchone()

                    if row:
                        self.photo_path = row[0]
                        self.employee_id_var.set(row[1])   # <-- THIS fills the Employee ID field
                    else:
                        self.photo_path = None
                        self.employee_id_var.set("")

                    self.display_photo(self.photo_path)
        except Exception as e:
            self.display_photo(None)

    def enable_edit_mode(self):
        if not self.current_teacher_id:
            return messagebox.showwarning("Warning", "Select a teacher first")
        else: 
            ask = messagebox.askyesno("Confirm","Are you sure you want to edit this teacher? ")
        self.edit_mode = True
        self.set_fields_state("normal")
        self.add_btn.config(state="disabled")
        self.delete_btn.config(text="CANCEL", bg="#757575")
        self.update_btn.config(state="normal")
        self.edit_label.config(text="EDIT MODE", fg="white", bg="red")

    def delete_teacher(self):
        if self.delete_btn["text"] == "CANCEL":
            self.reset_ui_state()
            return
        if not self.current_teacher_id: return messagebox.showwarning("Warning", "Select a teacher first")
        if not messagebox.askyesno("Confirm", f"Delete this teacher record: {self.teacher_name_var.get().strip()}?"):
            return

        try:
            with db_connect() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("DELETE FROM teacher WHERE teacher_id=%s", (self.current_teacher_id,))
                    conn.commit()
            messagebox.showinfo("Success", "Record deleted")
            self.reset_ui_state()
            self.load_teachers()
        except Exception as e:
            messagebox.showerror("Error", f"Delete failed: {e}")

    # ================= DATA LOADING & SMART PAGINATION =================
    def load_teachers(self):
        self.teacher_table.delete(*self.teacher_table.get_children())
        offset = (self.current_page - 1) * self.page_size
        try:
            with db_connect() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT COUNT(*) FROM teacher")
                    self.total_teachers = cursor.fetchone()[0]
                    cursor.execute("SELECT teacher_id, teacher_name, department FROM teacher ORDER BY teacher_name LIMIT %s OFFSET %s", (self.page_size, offset))
                    for row in cursor.fetchall():
                        self.teacher_table.insert("", "end", values=row)

            total_p = max(1, (self.total_teachers + self.page_size - 1) // self.page_size)
            self.teacher_count_var.set(f"Total: {self.total_teachers} | Page {self.current_page}/{total_p}")
        except Exception as e:
            print(f"Load error: {e}")

    def search_teacher(self):
        keyword = self.search_var.get().strip()
        if not keyword: return self.clear_search()
        
        try:
            with db_connect() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT teacher_id, teacher_name, department FROM teacher WHERE teacher_name LIKE %s", (f"%{keyword}%",))
                    self.search_results = cursor.fetchall()
            
            if not self.search_results:
                messagebox.showinfo("Search", f"No results found for '{keyword}'")
                return self.clear_search()
            
            else :
                messagebox.showinfo("Search", f"Found {len(self.search_results)} results for: {keyword}")

            self.search_page = 1
            self.update_search_table()
        except Exception as e:
            print(f"Search error: {e}")

    def update_search_table(self):
        self.teacher_table.delete(*self.teacher_table.get_children())
        start = (self.search_page - 1) * self.page_size
        end = start + self.page_size
        for row in self.search_results[start:end]: 
            self.teacher_table.insert("", "end", values=row)
        
        total_p = max(1, (len(self.search_results) + self.page_size - 1) // self.page_size)
        self.teacher_count_var.set(f"Found: {len(self.search_results)} | Page {self.search_page}/{total_p}")

    def clear_search(self):
        self.search_var.set("")
        self.search_results = []
        self.current_page = 1
        self.load_teachers()
        self.reset_ui_state()

    def next_page(self):
        if self.search_var.get().strip():
            if self.search_page * self.page_size < len(self.search_results):
                self.search_page += 1
                self.update_search_table()
        elif self.current_page * self.page_size < self.total_teachers:
            self.current_page += 1
            self.load_teachers()

    def prev_page(self):
        if self.search_var.get().strip():
            if self.search_page > 1:
                self.search_page -= 1
                self.update_search_table()
        elif self.current_page > 1:
            self.current_page -= 1
            self.load_teachers()

    def live_search(self):
        keyword = self.search_var.get().strip()

        if not keyword:
            self.clear_search()
            return

        try:
            with db_connect() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        """
                        SELECT teacher_id, teacher_name, department
                        FROM teacher
                        WHERE teacher_name LIKE %s
                        OR department LIKE %s
                        """,
                        (f"%{keyword}%", f"%{keyword}%")
                    )
                    self.search_results = cursor.fetchall()

            self.search_page = 1
            self.update_search_table()

        except Exception as e:
            print(f"Live search error: {e}")