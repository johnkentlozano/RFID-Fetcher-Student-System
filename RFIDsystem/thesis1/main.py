import tkinter as tk
from tkinter import messagebox
import serial
import threading
import serial.tools.list_ports

from frames.login import LoginFrame
from frames.main_dashboard import MainDashboard
from frames.student_record import StudentRecord
from frames.teacher_record import TeacherRecord
from frames.fetcher_record import FetcherRecord
from frames.rfid_registration import RfidRegistration
from frames.history_log import RFIDHistory
from frames.report import Report
from frames.account import Account
from frames.Classroom import ClassroomFrame
from frames.overrride import OverrideFrame
from frames.signup import SignUpFrame
from frames.forgot_password import ForgotPasswordFrame
from frames.adminoverride import AdminOverrideFrame
from frames.admin_record import AdminRecord

class Rfid(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("RFID MANAGEMENT SYSTEM - Cainta Catholic College")
        self.geometry("1350x700+0+0")

        self.current_user = None 
        self.current_frame_name = "LoginFrame"
        self.ser = None
        self.running = True 

        self.container = tk.Frame(self)
        self.container.pack(fill="both", expand=True)

        self.frames = {}

        for FrameClass in (LoginFrame, SignUpFrame, ForgotPasswordFrame):
            frame = FrameClass(self.container, self)
            self.frames[FrameClass.__name__] = frame
            frame.place(relwidth=1, relheight=1)

        self.show_frame("LoginFrame")
        
        self.start_serial_listener()

    def show_frame(self, name):
        restricted_pages = [
            "MainDashboard", "StudentRecord", "TeacherRecord","ClassroomFrame","admin_record",
            "FetcherRecord", "RfidRegistration","OverrideFrame","AdminOverrideFrame", "RFIDHistory", 
            "Report", "Account"
        ]
        
        # Security & Role Checks
        if name in restricted_pages and self.current_user is None:
            self.show_frame("LoginFrame")
            return

        if self.current_user and self.current_user.get("role") == "Teacher":
            admin_only = ["TeacherRecord", "RfidRegistration", "StudentRecord", "FetcherRecord", "RFIDHistory", "Report", "Account"]
            if name in admin_only:
                messagebox.showwarning("Access Denied", "Teachers do not have permission to access this module.")
                return

        # Navigation logic
        self.current_frame_name = name
        self.frames[name].tkraise()

    def dispatch_rfid(self, uid):
        dashboard = self.frames.get("MainDashboard")

        if dashboard and hasattr(dashboard, "current_frame") and dashboard.current_frame:
            active_frame = dashboard.current_frame
        else:
            active_frame = self.frames.get(self.current_frame_name)

        if not active_frame:
            return

        if hasattr(active_frame, "handle_rfid_tap"):
            active_frame.handle_rfid_tap(uid)

        elif hasattr(active_frame, "handle_rfid_scan"):
            active_frame.handle_rfid_scan(uid)

    def login_success(self, user_data):
        self.current_user = user_data  

        frame = MainDashboard(self.container, self)
        self.frames["MainDashboard"] = frame
        frame.place(relwidth=1, relheight=1)

        self.show_frame("MainDashboard")
        
    def start_serial_listener(self):
        def listen():
            # Auto-detect COM port
            ports = list(serial.tools.list_ports.comports())
            target_port = next((p.device for p in ports if any(x in p.description for x in ["USB", "CH340", "Arduino"])), "COM4")
            
            try:
                self.ser = serial.Serial(target_port, 9600, timeout=0.1)
                print(f"Connected to Arduino on {target_port}")
            except Exception as e:
                print(f"Serial Error: {e}")
                return

            while self.running:
                try:
                    if self.ser and self.ser.is_open and self.ser.in_waiting:
                        # Change this line inside start_serial_listener -> listen()
                        line = self.ser.readline().decode('utf-8', errors='ignore').strip().replace('\r', '')
                        if line:
                            # Clean the UID string (removes "UID Tag: " prefix if present)
                            uid = line.split(":")[-1].strip() if ":" in line else line
                            self.after(0, self.dispatch_rfid, uid)
                except:
                    break
            
            if self.ser: self.ser.close()

        thread = threading.Thread(target=listen, daemon=True)
        thread.start()

    def logout(self):
        self.current_user = None 
        for name in list(self.frames.keys()):
            if name not in ["LoginFrame", "SignUpFrame", "ForgotPasswordFrame"]:
                self.frames[name].destroy()
                del self.frames[name]
        self.show_frame("LoginFrame")

    def on_closing(self):
        self.running = False
        self.destroy()
        

if __name__ == "__main__":
    app = Rfid()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()