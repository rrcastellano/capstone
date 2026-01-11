import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import os

# Set client encoding to UTF8 to avoid locale issues
os.environ["PGCLIENTENCODING"] = "utf-8"

try:
    con = psycopg2.connect(dbname='postgres', user='postgres', password='ronaldo1', host='localhost', port='5432')
    con.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = con.cursor()
    # Check if exists
    cur.execute("SELECT 1 FROM pg_catalog.pg_database WHERE datname = 'CS50'")
    exists = cur.fetchone()
    if not exists:
        cur.execute('CREATE DATABASE "CS50"')
        print("Database CS50 created successfully")
    else:
        print("Database CS50 already exists")
except Exception as e:
    print(f"Error: {e}")
finally:
    if 'cur' in locals():
        cur.close()
    if 'con' in locals():
        con.close()
