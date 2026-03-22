import sqlite3
c = sqlite3.connect('sql_app.db')
print(c.execute("SELECT sql FROM sqlite_master WHERE name='subjects'").fetchone()[0])
