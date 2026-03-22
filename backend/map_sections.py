import sqlite3
import traceback
try:
    conn = sqlite3.connect('sql_app.db')
    
    # Get sections
    sec_A = conn.execute("SELECT id FROM sections WHERE name='Section A'").fetchone()[0]
    sec_B = conn.execute("SELECT id FROM sections WHERE name='Section B'").fetchone()[0]
    sec_C = conn.execute("SELECT id FROM sections WHERE name='Section C'").fetchone()[0]
    
    # Get mentors
    men_A = conn.execute("SELECT f.id FROM faculty f JOIN users u ON f.user_id = u.id WHERE u.username='mentor_a'").fetchone()[0]
    men_B = conn.execute("SELECT f.id FROM faculty f JOIN users u ON f.user_id = u.id WHERE u.username='mentor_b'").fetchone()[0]
    men_C = conn.execute("SELECT f.id FROM faculty f JOIN users u ON f.user_id = u.id WHERE u.username='mentor_c'").fetchone()[0]

    # Update students
    conn.execute('UPDATE students SET section_id = ? WHERE mentor_id = ?', (sec_A, men_A))
    conn.execute('UPDATE students SET section_id = ? WHERE mentor_id = ?', (sec_B, men_B))
    conn.execute('UPDATE students SET section_id = ? WHERE mentor_id = ?', (sec_C, men_C))
    conn.commit()
    print('Students updated with section IDs successfully.')
except Exception as e:
    traceback.print_exc()
