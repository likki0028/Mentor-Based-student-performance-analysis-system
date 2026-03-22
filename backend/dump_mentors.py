import sqlite3

connection = sqlite3.connect("h:/mini project/vibe/backend/sql_app.db")
cursor = connection.cursor()

with open("mentors.txt", "w") as f:
    f.write("--- ALL USERS ---\n")
    cursor.execute("SELECT id, username, role, is_active FROM users")
    users = cursor.fetchall()
    for row in users:
        f.write(str(row) + "\n")
        
connection.close()
