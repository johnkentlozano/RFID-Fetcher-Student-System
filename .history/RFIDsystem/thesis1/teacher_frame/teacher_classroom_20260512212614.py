
            
    def clear_entire_class(self):
        # 1. First Warning
        if not messagebox.askyesno("Confirm Reset", "Are you sure you want to remove ALL students from your class for the new school year?"):
            return
            
        # 2. Final Warning (Safety First!)
        if not messagebox.askretrycancel("Final Warning", "This action cannot be undone. Proceed?"):
            return

        try:
            with db_connect() as conn:
                with conn.cursor() as cur:
                    # Deletes only the students linked to THIS teacher
                    cur.execute("DELETE FROM classroom WHERE teacher_name = %s", (self.real_teacher_name,))
                    conn.commit()
            
            self.refresh_tables()
            self.info_label.config(text="Classroom Cleared.")
            messagebox.showinfo("Success", "Classroom is now empty. You can begin adding new students.")
        except Exception as e:
            messagebox.showerror("Database Error", f"Could not reset class: {e}")
            
    def load_user(self, user_data):
        self.user_data = user_data
        self.username = user_data.get("username")
        self.employee_id = user_data.get("employee_id")

    # safe default (IMPORTANT)
        self.department = user_data.get("department", "No Department")

    # NOW it's safe to call this
        self.real_teacher_name = self.get_teacher_display_name()

    # update label safely
        self.teacher_label.config(
        text=f"Active: {self.real_teacher_name} | {self.department}"
        )

        if not self.check_for_updates_started:
            self.check_for_updates_started = True
            self.after(1500, self.check_for_updates)

        print("Loaded user:", self.username)