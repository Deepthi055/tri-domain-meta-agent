import sqlite3
conn = sqlite3.connect('tridomain.db')
cursor = conn.cursor()
print('users schema:')
for row in cursor.execute('PRAGMA table_info("users")'):
    print(row)
conn.close()
