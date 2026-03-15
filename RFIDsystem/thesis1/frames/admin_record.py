import tkinter as tk
from tkinter import messagebox, filedialog, ttk
from PIL import ImageTk, Image
import os
import sys
import io

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from utils.database import db_connect


class AdminRecord(tk.Frame):

    def __init__(self, parent, controller):
        super().__init__(parent, bg="#b2e5ed")
        self.controller = controller

        self.photo_path = None
        self.photo = None
        self.edit_mode = False
        self.current_admin_id = None

        self.page_size = 50
        self.current_page = 1
        self.total_admins = 0
        self.search_results = []
        self.search_page = 1

        header = tk.Frame(self, height=70, bg="#0047AB")
        header.pack(fill="x")

        tk.Label(
            header,
            text="ADMIN INFORMATION",
            font=("Arial", 20, "bold"),
            bg="#0047AB",
            fg="white"
        ).place(x=30, y=18)

        # ================= LEFT PANEL =================

        self.left_box = tk.Frame(self, width=430, height=480, bg="white", bd=2, relief="groove")
        self.left_box.place(x=40, y=90)
        self.left_box.pack_propagate(False)

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

        # ================= VARIABLES =================

        self.admin_name_var = tk.StringVar()
        self.employee_id_var = tk.StringVar()

        self.num_validate = self.register(lambda v: v.isdigit() or v == "")

        tk.Label(self.left_box, text="Admin Name:", bg="white", font=("Arial", 11)).place(x=20, y=200)

        self.name_entry = tk.Entry(self.left_box, textvariable=self.admin_name_var, width=30, font=("Arial", 11))
        self.name_entry.place(x=150, y=200)

        tk.Label(self.left_box, text="Employee ID:", bg="white", font=("Arial", 11)).place(x=20, y=240)

        self.employee_id_entry = tk.Entry(
            self.left_box,
            textvariable=self.employee_id_var,
            width=30,
            font=("Arial", 11),
            validate="key",
            validatecommand=(self.num_validate, "%P")
        )

        self.employee_id_entry.place(x=150, y=240)

        # ================= BUTTONS =================

        btn_frame = tk.Frame(self.left_box, bg="white")
        btn_frame.place(x=15, y=320)

        self.add_btn = tk.Button(btn_frame, text="ADD", width=9, bg="#4CAF50", fg="white",
                                 font=("Arial", 9, "bold"), command=self.add_admin)

        self.add_btn.grid(row=0, column=0, padx=2)

        self.edit_btn = tk.Button(btn_frame, text="EDIT", width=9, bg="#2196F3", fg="white",
                                  font=("Arial", 9, "bold"), command=self.enable_edit_mode)

        self.edit_btn.grid(row=0, column=1, padx=2)

        self.update_btn = tk.Button(btn_frame, text="UPDATE", width=9, bg="#FF9800", fg="white",
                                    font=("Arial", 9, "bold"), command=self.update_admin_db, state="disabled")

        self.update_btn.grid(row=0, column=2, padx=2)

        self.delete_btn = tk.Button(btn_frame, text="DELETE", width=9, bg="#F44336", fg="white",
                                    font=("Arial", 9, "bold"), command=self.delete_admin)

        self.delete_btn.grid(row=0, column=3, padx=2)

        # ================= RIGHT PANEL =================

        self.right_panel = tk.Frame(self, width=500, height=480, bg="white", bd=2, relief="groove")
        self.right_panel.place(x=520, y=90)
        self.right_panel.pack_propagate(False)

        tk.Label(self.right_panel, text="Search Admin (NAME)", font=("Arial", 14, "bold"), bg="white").place(x=20, y=15)

        self.search_var = tk.StringVar()

        tk.Entry(self.right_panel, textvariable=self.search_var, width=25, font=("Arial", 11)).place(x=20, y=50)

        tk.Button(self.right_panel, text="Search", command=self.search_admin).place(x=260, y=47)
        tk.Button(self.right_panel, text="Clear", command=self.clear_search).place(x=320, y=47)

        self.admin_count_var = tk.StringVar(value="Total Records: 0")

        tk.Label(self.right_panel, textvariable=self.admin_count_var, font=("Arial", 11, "bold"),
                 fg="#0047AB", bg="white").place(x=20, y=85)

        columns = ("admin_id", "name", "role")

        self.admin_table = ttk.Treeview(self.right_panel, columns=columns, show="headings", height=12)

        self.admin_table.heading("admin_id", text="ID")
        self.admin_table.heading("name", text="Admin Name")
        self.admin_table.heading("role", text="Role")

        self.admin_table.column("admin_id", width=50)
        self.admin_table.column("name", width=240)
        self.admin_table.column("role", width=120)

        self.admin_table.place(x=20, y=120, width=450)

        self.admin_table.bind("<<TreeviewSelect>>", self.on_select)

        self.reset_ui_state()
        self.load_admins()

    # ================= PHOTO =================

    def upload_photo(self):

        path = filedialog.askopenfilename(filetypes=[("Image Files","*.jpg *.png *.jpeg")])

        if path:
            self.photo_path = path
            img = Image.open(path).resize((160,160))
            self.photo = ImageTk.PhotoImage(img)
            self.photo_label.config(image=self.photo)

    def remove_photo_action(self):

        self.photo_path = None
        self.photo_label.config(image="")

    # ================= UI CONTROL =================

    def set_fields_state(self,state):

        self.name_entry.config(state=state)
        self.employee_id_entry.config(state=state)

    def reset_ui_state(self):

        self.edit_mode = False
        self.current_admin_id = None

        self.set_fields_state("disabled")

        self.add_btn.config(text="ADD")
        self.edit_btn.config(state="normal")
        self.delete_btn.config(text="DELETE")

        self.update_btn.config(state="disabled")
        self.edit_label.config(text="VIEW MODE")

        self.clear_fields()

    def clear_fields(self):

        self.admin_name_var.set("")
        self.employee_id_var.set("")
        self.photo_label.config(image="")

    # ================= CRUD =================

    def add_admin(self):

        if self.add_btn["text"] == "ADD":

            self.reset_ui_state()
            self.set_fields_state("normal")

            self.add_btn.config(text="SAVE")
            self.edit_btn.config(state="disabled")
            self.delete_btn.config(text="CANCEL")

            self.edit_label.config(text="ADD MODE")

            return

        try:

            binary_photo=None

            if self.photo_path:

                img=Image.open(self.photo_path).convert("RGB")
                buf=io.BytesIO()
                img.save(buf,format="JPEG")
                binary_photo=buf.getvalue()

            with db_connect() as conn:

                with conn.cursor() as cursor:

                    cursor.execute("""
                        INSERT INTO admin
                        (admin_name, employee_id, role, photo_path)
                        VALUES (%s,%s,'Admin',%s)
                    """,(
                        self.admin_name_var.get(),
                        self.employee_id_var.get(),
                        binary_photo
                    ))

                    conn.commit()

            messagebox.showinfo("Success","Admin added successfully")

            self.reset_ui_state()
            self.load_admins()

        except Exception as e:

            messagebox.showerror("Database Error",str(e))

    def load_admins(self):

        self.admin_table.delete(*self.admin_table.get_children())

        try:

            with db_connect() as conn:

                with conn.cursor() as cursor:

                    cursor.execute(
                        "SELECT admin_id, admin_name, role FROM admin ORDER BY admin_name"
                    )

                    rows=cursor.fetchall()

                    for row in rows:
                        self.admin_table.insert("", "end", values=row)

                    self.admin_count_var.set(f"Total Records: {len(rows)}")

        except Exception as e:
            print(e)

    def search_admin(self):

        keyword=self.search_var.get()

        with db_connect() as conn:
            with conn.cursor() as cursor:

                cursor.execute(
                    "SELECT admin_id, admin_name, role FROM admin WHERE admin_name LIKE %s",
                    (f"%{keyword}%",)
                )

                rows=cursor.fetchall()

                self.admin_table.delete(*self.admin_table.get_children())

                for row in rows:
                    self.admin_table.insert("", "end", values=row)

    def clear_search(self):

        self.search_var.set("")
        self.load_admins()


    def enable_edit_mode(self):

      selected = self.admin_table.focus()

      if not selected:
          messagebox.showwarning("Select", "Please select an admin first.")
          return

      data = self.admin_table.item(selected)["values"]

      self.current_admin_id = data[0]

      self.admin_name_var.set(data[1])

      self.set_fields_state("normal")

      self.edit_mode = True

      self.edit_label.config(text="EDIT MODE", fg="orange")

      self.update_btn.config(state="normal")

      self.add_btn.config(state="disabled")


    def update_admin_db(self):

      if not self.edit_mode or not self.current_admin_id:
          messagebox.showwarning("Error", "No admin selected for update.")
          return

      try:

          binary_photo = None

          if self.photo_path:
              img = Image.open(self.photo_path).convert("RGB")
              buf = io.BytesIO()
              img.save(buf, format="JPEG")
              binary_photo = buf.getvalue()

          with db_connect() as conn:
              with conn.cursor() as cursor:

                  if binary_photo:
                      cursor.execute("""
                          UPDATE admin
                          SET admin_name=%s, employee_id=%s, photo_path=%s
                          WHERE admin_id=%s
                      """, (
                          self.admin_name_var.get(),
                          self.employee_id_var.get(),
                          binary_photo,
                          self.current_admin_id
                      ))

                  else:
                      cursor.execute("""
                          UPDATE admin
                          SET admin_name=%s, employee_id=%s
                          WHERE admin_id=%s
                      """, (
                          self.admin_name_var.get(),
                          self.employee_id_var.get(),
                          self.current_admin_id
                      ))

                  conn.commit()

          messagebox.showinfo("Success", "Admin updated successfully")

          self.reset_ui_state()
          self.load_admins()

      except Exception as e:
          messagebox.showerror("Database Error", str(e))

    def delete_admin(self):

      selected = self.admin_table.focus()

      if not selected:
          messagebox.showwarning("Select", "Please select an admin to delete.")
          return

      data = self.admin_table.item(selected)["values"]
      admin_id = data[0]

      confirm = messagebox.askyesno(
          "Confirm Delete",
          "Are you sure you want to delete this admin?"
      )

      if not confirm:
          return

      try:
          with db_connect() as conn:
              with conn.cursor() as cursor:

                  cursor.execute(
                      "DELETE FROM admin WHERE admin_id=%s",
                      (admin_id,)
                  )

                  conn.commit()

          messagebox.showinfo("Success", "Admin deleted successfully")

          self.reset_ui_state()
          self.load_admins()

      except Exception as e:
          messagebox.showerror("Database Error", str(e))

    def on_select(self, event):

      selected = self.admin_table.focus()

      if not selected:
          return

      data = self.admin_table.item(selected)["values"]

      admin_id = data[0]
      admin_name = data[1]

      self.current_admin_id = admin_id
      self.admin_name_var.set(admin_name)

      try:
          with db_connect() as conn:
              with conn.cursor() as cursor:

                  cursor.execute(
                      "SELECT employee_id, photo_path FROM admin WHERE admin_id=%s",
                      (admin_id,)
                  )

                  result = cursor.fetchone()

                  if result:
                      self.employee_id_var.set(result[0])

                      photo_blob = result[1]

                      if photo_blob:
                          stream = io.BytesIO(photo_blob)
                          img = Image.open(stream).resize((160,160))
                          self.photo = ImageTk.PhotoImage(img)
                          self.photo_label.config(image=self.photo)
                      else:
                          self.photo_label.config(image="")

      except Exception as e:
          print("Load Admin Error:", e)