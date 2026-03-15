import serial
import time
from PyQt5.QtCore import QThread, pyqtSignal

class SerialThread(QThread):
    uid_scanned = pyqtSignal(str)

    def __init__(self, port="COM4", baud=9600):
        super().__init__()
        self.port = port
        self.baud = baud
        self.ser = None
        self._running = True
        
    def run(self):
        try:
            self.ser = serial.Serial(self.port, self.baud, timeout=1)
            time.sleep(2) # Arduino Reset
            while self._running:
                if self.ser.in_waiting:
                    line = self.ser.readline().decode(errors="ignore").strip()
                    if line:
                        # Extract UID if format is "UID:XXXX" or just "XXXX"
                        clean_uid = line.split(":")[-1].strip().upper()
                        self.uid_scanned.emit(clean_uid)
                self.msleep(50) # Prevent CPU hogging
        except Exception as e:
            print(f"Hardware Error on {self.port}: {e}")

    def write(self, message):
        if self.ser and self.ser.is_open:
            # Map statuses to simple codes for Arduino (A=Auth, D=Denied)
            code = "A" if "AUTH" in message.upper() else "D"
            self.ser.write((code + "\n").encode())

    def stop(self):
        self._running = False
        if self.ser and self.ser.is_open:
            self.ser.close()
        self.quit()
        self.wait()