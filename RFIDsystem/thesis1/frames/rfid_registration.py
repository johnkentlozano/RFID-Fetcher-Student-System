import tkinter as tk
from tkinter import messagebox, ttk, filedialog
import sys, os
from PIL import Image, ImageTk
import io

# ================= PATH SETUP =================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

from utils.database import db_connect

class RfidRegistration(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#b2e5ed")
        self.controller = controller
        
        # State Management
        self.selected_registration_id = None
        self.mode = "view" 

        # Variables (Access Code Removed)
        self.rfid_var = tk.StringVar()          
        self.fetcher_name_var = tk.StringVar()
        self.fetcher_code_var = tk.StringVar()      
        self.fetcher_address_var = tk.StringVar()      
        self.fetcher_contact_var = tk.StringVar()

        

        self.paired_rfid_var = tk.StringVar()    
        self.student_rfid_var = tk.StringVar()   
        self.student_id_var = tk.StringVar()
        self.student_name_var = tk.StringVar()
        self.grade_var = tk.StringVar()        
        self.teacher_var = tk.StringVar()
        
        self.search_var = tk.StringVar()
        
        self.fetcher_code_var.trace_add("write", self.auto_fill_fetcher_details)
        self.fetcher_code_var.trace_add("write", self.enforce_fc_prefix)

        self.student_id_var.trace_add("write", self.auto_fill_student_details)


        self.student_rfid_var.trace_add("write", self.sync_student_to_link)
        self.search_var.trace_add("write", lambda *args: self.load_data())

        self.contact_validator = self.register(self.validate_contact)
         
        self.setup_ui()
        self.reset_load()

    def sync_student_to_link(self, *args):
        if self.mode != "view":
            self.paired_rfid_var.set(self.student_rfid_var.get())
            

    def setup_ui(self):
        header = tk.Frame(self, bg="#0047AB", height=50)
        header.pack(fill="x")
        tk.Label(header, text="RFID REGISTRATION & PAIRING",
                 font=("Helvetica", 16, "bold"), bg="#0047AB", fg="white").pack(pady=10)
        
        # --- TOP SECTION: COMPACT SPLIT LAYOUT ---
        top_container = tk.Frame(self, bg="#b2e5ed")
        top_container.pack(fill="x", padx=15, pady=5)
        top_container.columnconfigure(0, weight=1)
        top_container.columnconfigure(1, weight=1)

        # LEFT SIDE: FETCHER
        fetcher_frame = tk.LabelFrame(top_container, text=" FETCHER DETAILS ", font=("Arial", 10, "bold"), bg="white", padx=10, pady=5)
        fetcher_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        
        self.fetcher_photo_lbl = self.create_photo_box(fetcher_frame)
        self.fetcher_entries = self.create_form(fetcher_frame, [
            ("Fetcher RFID", self.rfid_var),
            ("Paired Link", self.paired_rfid_var),
            ("Fetcher Code", self.fetcher_code_var),
            ("Full Name", self.fetcher_name_var),          
            ("Address", self.fetcher_address_var),   
            ("Contact", self.fetcher_contact_var)
        ])

        # RIGHT SIDE: STUDENT
        student_frame = tk.LabelFrame(top_container, text=" STUDENT DETAILS ", font=("Arial", 10, "bold"), bg="white", padx=10, pady=5)
        student_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        
        self.student_photo_lbl = self.create_photo_box(student_frame)
        self.student_entries = self.create_form(student_frame, [
            ("Student RFID", self.student_rfid_var),
            ("Student ID", self.student_id_var),
            ("Full Name", self.student_name_var),
            ("Grade/Sec", self.grade_var),
            ("Adviser", self.teacher_var)
        ])

        # --- CENTER SECTION: ACTION BUTTONS ---
        btn_container = tk.Frame(self, bg="#b2e5ed")
        btn_container.pack(pady=5)
        
        btn_style = {"font": ("Arial", 9, "bold"), "width": 12, "fg": "white", "relief": "raised", "bd": 1}
        
        self.add_btn = tk.Button(btn_container, text="NEW", bg="#2ecc71", command=self.toggle_add, **btn_style)
        self.add_btn.grid(row=0, column=0, padx=3)
        
        self.edit_btn = tk.Button(btn_container, text="EDIT", bg="#3498db", command=self.toggle_edit, **btn_style)
        self.edit_btn.grid(row=0, column=1, padx=3)
        
        # THE NEW CLEAR BUTTON
        self.clear_btn = tk.Button(btn_container, text="CLEAR INPUT", bg="#95a5a6", command=self.clear_all, **btn_style)
        self.clear_btn.grid(row=0, column=2, padx=3)

        self.status_btn = tk.Button(btn_container, text="STATUS", bg="#f39c12", command=self.toggle_status, **btn_style)
        self.status_btn.grid(row=0, column=3, padx=3)

        self.delete_btn = tk.Button(btn_container, text="DELETE", bg="#e74c3c", command=self.handle_delete_cancel, **btn_style)
        self.delete_btn.grid(row=0, column=4, padx=3)

        # --- SEARCH BAR ---
        search_frame = tk.Frame(self, bg="#b2e5ed")
        search_frame.pack(fill="x", padx=20, pady=5)
        tk.Label(search_frame, text="🔍 Search:", font=("Arial", 10, "bold"), bg="#b2e5ed").pack(side="left")
        tk.Entry(search_frame, textvariable=self.search_var, font=("Arial", 10), width=35).pack(side="left", padx=10)
        tk.Button(search_frame, text="Reset Search", font=("Arial", 8), command=lambda: self.search_var.set("")).pack(side="left")

        # --- BOTTOM SECTION: DATA TABLE ---
        table_frame = tk.Frame(self, bg="white", bd=1, relief="sunken")
        table_frame.pack(fill="both", expand=True, padx=20, pady=(0, 15))

        # In setup_ui, update your columns to include the Code
        cols = ("id", "s_name", "f_name", "f_code", "status")
        self.table = ttk.Treeview(table_frame, columns=cols, show="headings", height=8)
        
        headings = {
            "id": "ID", 
            "s_name": "STUDENT", 
            "f_name": "FETCHER", 
            "f_code": "CODE", 
            "status": "STATUS"
        }
        
        for col in cols:
            self.table.heading(col, text=headings[col])
            self.table.column(col, anchor="center")
        
        self.table.pack(fill="both", expand=True)
        self.table.bind("<<TreeviewSelect>>", self.on_row_select)

    def create_photo_box(self, parent):
        frame = tk.Frame(parent, bg="white")
        frame.pack(pady=5)
        
        # Removed width=12, height=4 (text units)
        # Added a fixed pixel size for the "empty" state
        container = tk.Label(frame, text="No Photo", bg="#ecf0f1", 
                             width=20, height=10, # Adjusted for a better "empty" look
                             relief="solid", bd=1)
        container.pack()
        container.image_bytes = None 
        
        btn_f = tk.Frame(frame, bg="white")
        btn_f.pack(fill="x", pady=2)
        
        # Slightly larger buttons for better accessibility
        tk.Button(btn_f, text="Set Photo", font=("Arial", 8), 
                  command=lambda: self.upload_photo(container)).pack(side="left", expand=True, padx=2)
        tk.Button(btn_f, text="Clear", font=("Arial", 8), 
                  command=lambda: self.remove_photo(container)).pack(side="left", expand=True, padx=2)
        return container

    def create_form(self, parent, fields):
        frame = tk.Frame(parent, bg="white")
        frame.pack(fill="x", pady=5)
        entries = []
        for i,(label,var) in enumerate(fields):

            tk.Label(frame,text=label,bg="white",font=("Arial",8)).grid(row=i,column=0,sticky="e",pady=1,padx=5)

            if label == "Grade/Sec":
                ent = ttk.Combobox(frame,textvariable=var,
                                values=["Kinder 1","Kinder 2","1","2","3","4","5","6"],
                                state="readonly",width=20)

            elif label == "Adviser":
                ent = ttk.Combobox(frame,textvariable=var,
                                values=self.get_teacher_list(),
                                state="readonly",width=20)

            elif label == "Contact":
                ent = tk.Entry(frame,textvariable=var,font=("Arial",9),
                            width=22,
                            validate="key",
                            validatecommand=(self.contact_validator,"%P"))

            else:
                ent = tk.Entry(frame,textvariable=var,font=("Arial",9),width=22)

            ent.grid(row=i,column=1,pady=1,padx=5,sticky="w")
            entries.append(ent)
        return entries

    def remove_photo(self, target):
        if self.mode == "view": return
        target.config(image="", text="No Photo")
        target.image_bytes = None

    def save_record(self):
        # 1. Gather Input Data
        f_code = self.fetcher_code_var.get().strip()  # The PRIMARY link (FC_XXXX)
        f_rfid = self.rfid_var.get().strip()          # The physical tag data
        f_name = self.fetcher_name_var.get().strip()
        f_address = self.fetcher_address_var.get().strip()
        f_contact = self.fetcher_contact_var.get().strip()

        s_id = self.student_id_var.get().strip()
        s_name = self.student_name_var.get().strip()
        s_rfid = self.student_rfid_var.get().strip()
        grade = self.grade_var.get().strip()
        teacher = self.teacher_var.get().strip()
        
        # Photo handling
        s_photo = getattr(self.student_photo_lbl, 'image_bytes', None)
        f_photo = getattr(self.fetcher_photo_lbl, 'image_bytes', None)
        
        # --- AUTO-GENERATE FETCHER CODE IF EMPTY ---
        if not f_code and self.mode == "add":
            f_code = self.generate_fetcher_code() 
            self.fetcher_code_var.set(f_code)

        # Validation
        if not all([f_code, s_id, f_name]):
            messagebox.showerror("Error", "Fetcher Code, Student ID, and Name are required!")
            return

        try:
            with db_connect() as conn:
                with conn.cursor(dictionary=True) as cur:
                    
                    # STEP 1: UPSERT STUDENT (Parent 1)
                    sql_s = """INSERT INTO student (Student_id, Student_name, grade_lvl, student_rfid, 
                               photo_path, Guardian_name, Guardian_contact, created_at) 
                               VALUES (%s, %s, %s, %s, %s, %s, %s, CURDATE())
                               ON DUPLICATE KEY UPDATE Student_name=%s, grade_lvl=%s, student_rfid=%s, 
                               photo_path=IFNULL(%s, photo_path)"""
                    cur.execute(sql_s, (s_id, s_name, grade, s_rfid, s_photo, f_name, f_contact, 
                                        s_name, grade, s_rfid, s_photo))

                    # STEP 2: UPSERT FETCHER (Parent 2 - The FK Source)
                    sql_f = """INSERT INTO fetcher (fetcher_code, fetcher_name, Address, contact, photo_path, created_at) 
                               VALUES (%s, %s, %s, %s, %s, CURDATE())
                               ON DUPLICATE KEY UPDATE fetcher_name=%s, Address=%s, contact=%s, 
                               photo_path=IFNULL(%s, photo_path)"""
                    cur.execute(sql_f, (f_code, f_name, f_address, f_contact, f_photo, 
                                        f_name, f_address, f_contact, f_photo))

                    # STEP 3: MANAGE REGISTRATION LINK (The Child)
                    if self.mode == "edit":
                        sql_reg = """UPDATE registrations SET 
                                    fetcher_code=%s, rfid=%s, fetcher_name=%s, student_id=%s, 
                                    student_name=%s, grade=%s, teacher=%s, address=%s, contact=%s, 
                                    paired_rfid=%s, student_rfid=%s, photo_path=%s, fetcher_photo_path=%s 
                                    WHERE registration_id=%s"""
                        val_reg = (f_code, f_rfid, f_name, s_id, s_name, grade, teacher,
                                    f_address, f_contact, 
                                    s_rfid, s_rfid, s_photo, f_photo, self.selected_registration_id)
                    else:
                        sql_reg = """INSERT INTO registrations 
                                    (fetcher_code, rfid, fetcher_name, student_id, 
                                    student_name, grade, teacher, address, contact, 
                                    paired_rfid, student_rfid, status, photo_path, fetcher_photo_path) 
                                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'Active',%s,%s)"""
                        val_reg = (f_code, f_rfid, f_name, s_id, s_name, grade, teacher,
                                    f_address, f_contact, 
                                    s_rfid, s_rfid, s_photo, f_photo)
                    
                    cur.execute(sql_reg, val_reg)
                    conn.commit()

            messagebox.showinfo("Success", f"Records synced! Assigned Code: {f_code}")
            
            if messagebox.askyesno("Link Sibling", f"Link another student to {f_name}?"):
                self.student_id_var.set(""); self.student_name_var.set("")
                self.student_rfid_var.set(""); self.grade_var.set("")
                self.display_blob(self.student_photo_lbl, None)
                self.mode = "add"
            else:
                self.reset_load()
                
        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to sync: {str(e)}")
            
            
    def toggle_add(self):
        if self.mode == "view":
            self.mode = "add"
            self.clear_all()
            self.fetcher_code_var.set("FC_")
            self.unlock_ui()
            self.add_btn.config(text="SAVE", bg="#27ae60")
            self.edit_btn.config(state="disabled")
            self.delete_btn.config(text="CANCEL")
        else:
            self.save_record()

    def toggle_edit(self):
        if not self.selected_registration_id:
            messagebox.showwarning("Selection Required", "Please select a record to edit.")
            return
        if self.mode == "view":
            self.mode = "edit"
            self.unlock_ui()
            self.edit_btn.config(text="UPDATE", bg="#2980b9")
            self.add_btn.config(state="disabled")
            self.delete_btn.config(text="CANCEL")
        else:
            self.save_record()
            
    def on_row_select(self, event):
        if self.mode != "view": return
        item = self.table.focus()
        if not item: return
        self.selected_registration_id = self.table.item(item, "values")[0]
        try:
            with db_connect() as conn:
                with conn.cursor(dictionary=True) as cur:
                    cur.execute("SELECT * FROM registrations WHERE registration_id=%s", (self.selected_registration_id,))
                    r = cur.fetchone()
                    if r:
                        self.fetcher_code_var.set(r.get('fetcher_code', '') or "")
                        self.rfid_var.set(r.get('rfid', '') or "")
                        self.fetcher_name_var.set(r.get('fetcher_name', '') or "")
                        self.fetcher_address_var.set(r.get('address', '') or "")
                        self.fetcher_contact_var.set(r.get('contact', '') or "")

                        self.student_id_var.set(r.get('student_id', '') or "")
                        self.student_name_var.set(r.get('student_name', '') or "")
                        self.grade_var.set(r.get('grade', '') or "")
                        self.teacher_var.set(r.get('teacher', '') or "")
                        self.student_rfid_var.set(r.get('student_rfid', '') or "")
                        self.paired_rfid_var.set(r.get('paired_rfid', '') or "")

                        self.display_blob(self.student_photo_lbl, r['photo_path'])
                        self.display_blob(self.fetcher_photo_lbl, r['fetcher_photo_path'])
        except Exception as e: 
            print(f"Selection error: {e}")


    def toggle_status(self):
        # 1. Get the selected item
        selected_item = self.table.focus()
        
        # 2. Check if anything is actually selected
        if not selected_item:
            messagebox.showwarning("Selection Required", "Please select a record from the table first.")
            return
            
        # 3. Safely get the values
        item_data = self.table.item(selected_item)
        values = item_data.get("values")
        
        # 4. Check if values exist and have enough columns
        if not values or len(values) < 5:
            return

        # Now it is safe to access index 4
        current_status = values[4]
        new_status = "Inactive" if current_status == "Active" else "Active"
        
        try:
            with db_connect() as conn:
                with conn.cursor() as cur:
                    cur.execute("UPDATE registrations SET status=%s WHERE registration_id=%s", 
                                (new_status, self.selected_registration_id))
                    conn.commit()
            
            # Refresh the table to show the change
            self.load_data()
        except Exception as e:
            messagebox.showerror("Database Error", str(e))

    def load_data(self):
        self.table.delete(*self.table.get_children())
        search = f"%{self.search_var.get()}%"
        with db_connect() as conn:
            with conn.cursor() as cur:
                # Added 'fetcher_code' to the SELECT and the WHERE clause
                sql = """SELECT registration_id, student_name, fetcher_name, fetcher_code, status 
                         FROM registrations 
                         WHERE student_name LIKE %s 
                         OR fetcher_name LIKE %s 
                         OR fetcher_code LIKE %s 
                         OR student_id LIKE %s"""
                cur.execute(sql, (search, search, search, search))
                for row in cur.fetchall(): 
                    self.table.insert("", "end", values=row)

    def reset_load(self):
        self.mode = "view"; self.clear_all(); self.lock_ui()
        self.add_btn.config(text="NEW", bg="#2ecc71")
        self.edit_btn.config(text="EDIT", state="normal")
        self.delete_btn.config(text="DELETE")
        self.load_data()

    def handle_delete_cancel(self):
        if self.mode != "view": self.reset_load()
        else:
            if not self.selected_registration_id: return
            if messagebox.askyesno("Delete", "Delete this record?"):
                with db_connect() as conn:
                    with conn.cursor() as cur:
                        cur.execute("DELETE FROM registrations WHERE registration_id=%s", (self.selected_registration_id,))
                        conn.commit()
                self.reset_load()

    def clear_all(self):
        """Clears all input fields and resets to default images"""
        # 1. Reset the underlying data attributes
        # Use 'self.default_bytes' assuming you stored it during initialization
        self.student_photo_lbl.image_bytes =  None
        self.fetcher_photo_lbl.image_bytes = None
        
        # 2. Clear all StringVar variables
        vars_to_clear = [
            self.rfid_var, self.student_rfid_var, self.student_id_var, 
            self.fetcher_name_var, self.student_name_var, self.grade_var, 
            self.teacher_var, self.fetcher_address_var, self.fetcher_contact_var, 
            self.paired_rfid_var
        ]
        for v in vars_to_clear:
            v.set("")
        
        # 3. Visually update the photos to the default placeholder
        self.set_default_ui_photos()
        
        # 4. Reset state trackers
        self.selected_registration_id = None

        self.fetcher_code_var.set("FC_")
        

    def lock_ui(self):
        for e in self.fetcher_entries + self.student_entries: e.config(state="disabled")
    def unlock_ui(self):
        for e in self.fetcher_entries + self.student_entries: e.config(state="normal")
        
    def get_default_photo_bytes(self):
        try:
            # Make sure you have a 'default_user.png' in your assets or project folder
            default_path = os.path.join(BASE_DIR, "assets", "default.png") 
            
            if os.path.exists(default_path):
                img = Image.open(default_path).resize((100, 100))
                buf = io.BytesIO()
                img.save(buf, format='PNG')
                return buf.getvalue()
            return None # Or return a hardcoded empty byte string if file is missing
        except:
            return None
        
    def set_default_ui_photos(self):
        """Sets both photo boxes to the default asset or placeholder."""
        default_bytes = self.get_default_photo_bytes()

        if default_bytes:
            # Trigger display_blob with the default data
            self.display_blob(self.student_photo_lbl, default_bytes)
            self.display_blob(self.fetcher_photo_lbl, default_bytes)
            # We set image_bytes to None because we don't want to SAVE the 
            # default placeholder into the database for every record.
            self.student_photo_lbl.image_bytes = None
            self.fetcher_photo_lbl.image_bytes = None
        else:
            self.display_blob(self.student_photo_lbl, None)
            self.display_blob(self.fetcher_photo_lbl, None)
            
    def upload_photo(self, target):
        if self.mode == "view": return
        path = filedialog.askopenfilename(filetypes=[("Images", "*.jpg *.png *.jpeg")])
        if path:
            # Increased to 180x180 for better visibility
            img = Image.open(path).resize((180, 180), Image.Resampling.LANCZOS)
            buf = io.BytesIO()
            img.save(buf, format='PNG')
            target.image_bytes = buf.getvalue()
            photo = ImageTk.PhotoImage(img)
            target.config(image=photo, text="", width=180, height=180) # Force pixel size
            target.image = photo
            
    def display_blob(self, target, blob):
        """Standardized method to render BLOB data into a Label."""
        if blob:
            try:
                # Use 180x180 to match your upload_photo logic
                img = Image.open(io.BytesIO(blob)).resize((180, 180), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                target.config(image=photo, text="", width=180, height=180)
                target.image = photo  # Keep a reference!
                target.image_bytes = blob
            except Exception as e:
                print(f"Error displaying blob: {e}")
                self.remove_photo(target)
        else:
            # Revert to the "No Photo" placeholder look
            target.config(image="", text="No Photo", width=20, height=10) 
            target.image_bytes = None
            target.image = None
            
    def auto_fill_student_details(self, *args):
        sid = self.student_id_var.get().strip()
        if not sid:
            return

        try:
            with db_connect() as conn:
                with conn.cursor(dictionary=True) as cur:
                    cur.execute("""
                        SELECT 
                            s.Student_name,
                            s.grade_lvl,
                            s.student_rfid,
                            s.photo_path,
                            r.teacher
                        FROM student s
                        LEFT JOIN registrations r ON s.Student_id = r.student_id
                        WHERE s.Student_id = %s
                        LIMIT 1
                    """, (sid,))
                    res = cur.fetchone()

                    if res:
                        self.student_name_var.set(res['Student_name'])
                        self.grade_var.set(res['grade_lvl'])
                        self.student_rfid_var.set(res['student_rfid'])
                        self.teacher_var.set(res.get('teacher', '') or "")

                        # ✅ THIS IS THE MISSING PART
                        self.display_blob(self.student_photo_lbl, res['photo_path'])

                    else:
                        self.student_name_var.set("")
                        self.grade_var.set("")
                        self.student_rfid_var.set("")
                        self.display_blob(self.student_photo_lbl, None)

        except Exception as e:
            print("Auto-fill error:", e)

    def auto_fill_fetcher_details(self, *args):

        fcode = self.fetcher_code_var.get().strip()
        if not fcode:
            return

        try:
            with db_connect() as conn:
                with conn.cursor(dictionary=True) as cur:
                    cur.execute("""
                    SELECT 
                        f.fetcher_name,
                        f.Address,
                        f.contact,
                        f.photo_path,
                        r.rfid
                    FROM fetcher f
                    LEFT JOIN registrations r ON f.fetcher_code = r.fetcher_code
                    WHERE f.fetcher_code = %s
                    LIMIT 1
                                        """, (fcode,))
                    res = cur.fetchone()

                    if res:
                        self.fetcher_name_var.set(res['fetcher_name'])
                        self.fetcher_address_var.set(res['Address'] or "")
                        self.fetcher_contact_var.set(res['contact'] or "")
                        self.rfid_var.set(res.get('rfid', '') or "")
                        self.display_blob(self.fetcher_photo_lbl, res['photo_path'])
                    else:
                    # Optional: clear if not found
                        self.fetcher_name_var.set("")
                        self.fetcher_address_var.set("")
                        self.fetcher_contact_var.set("")
                        self.display_blob(self.fetcher_photo_lbl, None)

        except Exception as e:
            print(f"Auto-fill fetcher error: {e}")
            
    def generate_fetcher_code(self):
        """Generates a unique FC_XXXX code if the RFID field is empty."""
        try:
            with db_connect() as conn:
                with conn.cursor() as cur:
                    # Look for the highest FC_ number in the fetcher table
                    cur.execute("""
                        SELECT fetcher_code 
                        FROM fetcher 
                        WHERE fetcher_code LIKE 'FC_%' 
                        ORDER BY fetcher_code DESC LIMIT 1
                    """)
                    last_code = cur.fetchone()
                    
                    if last_code:
                        # last_code[0] is 'FC_0005', we split at '_' and take the number
                        try:
                            last_num = int(last_code[0].split('_')[1])
                            new_num = last_num + 1
                        except (IndexError, ValueError):
                            new_num = 1
                    else:
                        new_num = 1
                        
                    # Returns format: FC_0001, FC_0002, etc.
                    return f"FC_{new_num:04d}"
        except Exception as e:
            print(f"Code Generation Error: {e}")
            return "FC_ERROR"
    
    def handle_rfid_tap(self, uid):
        if self.mode == "view":
            return

        # Detect which field is currently focused
        focused = self.focus_get()

        if focused in self.fetcher_entries:
            self.rfid_var.set(uid)
            print("Fetcher RFID filled")

        elif focused in self.student_entries:
            self.student_rfid_var.set(uid)
            print("Student RFID filled")

        else:
            # Default behavior if no specific field focused
            if not self.rfid_var.get():
                self.rfid_var.set(uid)
            else:
                self.student_rfid_var.set(uid)
    
    def enforce_fc_prefix(self, *args):
        value = self.fetcher_code_var.get()
        if not value.startswith("FC_"):
            self.fetcher_code_var.set("FC_")

    def validate_contact(self, value):
        if value.isdigit() and len(value) <= 11:
            return True
        if value == "":
            return True
        return False
    
    def get_teacher_list(self):
        try:
            with db_connect() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT teacher_name FROM teacher")
                    return [r[0] for r in cur.fetchall()]
        except:
            return []
