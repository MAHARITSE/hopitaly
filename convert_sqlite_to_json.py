#!/usr/bin/env python
"""
Convert SQLite database (db.sqlite3) to JSON (db.json) for the JSON backend.
Run this after configuring DATABASES to use json_database.
"""
import sqlite3
import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

sqlite_path = os.path.join(BASE_DIR, 'db.sqlite3')
json_path = os.path.join(BASE_DIR, 'db.json')

if not os.path.exists(sqlite_path):
    print("No db.sqlite3 found. Nothing to convert.")
    exit(0)

conn = sqlite3.connect(sqlite_path)
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = [r[0] for r in cursor.fetchall()]

data = {}
for table in tables:
    cursor.execute('SELECT * FROM "%s"' % table)
    columns = [desc[0] for desc in cursor.description]
    rows = cursor.fetchall()
    table_data = []
    for row in rows:
        d = {}
        for i, col in enumerate(columns):
            val = row[i]
            d[col] = val
        table_data.append(d)
    data[table] = table_data

with open(json_path, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, default=str, ensure_ascii=False)

print("Converted %d tables to %s" % (len(tables), json_path))
print("Tables:", list(data.keys()))
