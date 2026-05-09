import mysql.connector

def db_connect():
    return mysql.connector.connect(
        host="127.0.0.1",
        user="root",
        password="johnjohn6581506",
        database="rfid_system",
    )
# # johnjohn6581506