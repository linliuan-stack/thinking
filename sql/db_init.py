#!/usr/bin/env python3
"""Database initializer — creates database and runs schema SQL files."""
import os
import psycopg2

DB_HOST = os.environ["DB_HOST"]
DB_PORT = os.environ["DB_PORT"]
DB_NAME = os.environ["DB_NAME"]
DB_USER = os.environ["DB_USER"]
DB_PASSWORD = os.environ["DB_PASSWORD"]

print(f"Connecting to PostgreSQL at {DB_HOST}:{DB_PORT}...")

conn = psycopg2.connect(host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASSWORD, dbname="postgres")
conn.autocommit = True
cur = conn.cursor()

cur.execute("SELECT 1 FROM pg_database WHERE datname=%s", (DB_NAME,))
if not cur.fetchone():
    cur.execute(f"CREATE DATABASE {DB_NAME}")
    print(f"Database '{DB_NAME}' created")
else:
    print(f"Database '{DB_NAME}' already exists")
conn.close()

conn2 = psycopg2.connect(host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASSWORD, dbname=DB_NAME)
conn2.autocommit = True
cur2 = conn2.cursor()

for sql_file in ["sql/init.sql", "sql/experiment.sql"]:
    with open(sql_file) as f:
        cur2.execute(f.read())
        print(f"Executed {sql_file}")

conn2.close()
print("DB init done")
