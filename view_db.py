import sqlite3
conn = sqlite3.connect("identities.db")
for r in conn.execute(
    "SELECT uid, label, name, sighting_count, ROUND(total_seconds, 1)"
    "FROM identities ORDER BY total_seconds DESC"):
    print(r)