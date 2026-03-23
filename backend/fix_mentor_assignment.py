import sqlite3
conn = sqlite3.connect('sql_app.db')
c = conn.cursor()

# Find niharika's faculty ID
c.execute("SELECT f.id FROM faculty f JOIN users u ON f.user_id = u.id WHERE u.username = 'niharika'")
row = c.fetchone()

if row:
    niharika_fac_id = row[0]
    print(f"Niharika's faculty ID: {niharika_fac_id}")
    
    # Update ALL students to point to niharika as mentor
    c.execute("UPDATE students SET mentor_id = ?", (niharika_fac_id,))
    conn.commit()
    print(f"Updated {c.rowcount} students to mentor_id = {niharika_fac_id}")
else:
    print("Niharika not found as faculty! Let's check all faculty:")
    c.execute("SELECT f.id, u.username, u.role FROM faculty f JOIN users u ON f.user_id = u.id")
    for r in c.fetchall():
        print(f"  Faculty ID {r[0]}: {r[1]} ({r[2]})")
    
    # Find niharika's user ID
    c.execute("SELECT id, role FROM users WHERE username = 'niharika'")
    u = c.fetchone()
    if u:
        print(f"\nNiharika user ID: {u[0]}, role: {u[1]}")
        # Check if she has a faculty entry
        c.execute("SELECT id FROM faculty WHERE user_id = ?", (u[0],))
        f = c.fetchone()
        if f:
            print(f"She has faculty ID: {f[0]}")
            c.execute("UPDATE students SET mentor_id = ?", (f[0],))
            conn.commit()
            print(f"Updated {c.rowcount} students!")
        else:
            print("Creating faculty entry for niharika...")
            c.execute("INSERT INTO faculty (user_id, employee_id) VALUES (?, 'FAC_NIK')", (u[0],))
            fac_id = c.lastrowid
            c.execute("UPDATE students SET mentor_id = ?", (fac_id,))
            conn.commit()
            print(f"Created faculty ID {fac_id} and updated {c.rowcount} students!")

# Verify
c.execute("SELECT mentor_id, COUNT(*) FROM students GROUP BY mentor_id")
print(f"\nVerification - students by mentor_id: {c.fetchall()}")

conn.close()
