# RFIDsystem
thesis2

# LOGIN PAGE 
- In login page have user input username, employee id, and password if correct go to maindashboard else incorrect input or missing fields 


# SIGN UP 
- Sign up the new admin user or the teacher 

# FORGOT PASSWORD 
- Change if the user forgot the password 

# DASHBOARD 
-( AMDIN )
- STUDENT RECORD 
    -- ADD STUDENT NAME 

🔹 RFID Tapping
Fix the system so that if the student taps first, the fetcher can still be recognized afterward.
Reduce the waiting time to 3–4 seconds only.

🔹 Master Card
Either:
The student taps first, then the teacher can authorize, or
The teacher taps first, then waits for the student tap.
 the fetcher taps once and has 3 students linked to their RFID, they should only need one tap, then wait for the students to tap.
The system should display the remaining students who still need to tap.
🔹 RFID Registration
Fix the Update function (it is currently not working).
Allow adding RFID records without relying only on foreign keys.
Improve validation and ensure proper linking between student and fetcher records.