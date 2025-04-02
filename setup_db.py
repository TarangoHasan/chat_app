import sqlite3

conn = sqlite3.connect('data.db')
c = conn.cursor()

# Users Table
c.execute('''CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    name TEXT,
    password TEXT,
    profile_picture TEXT DEFAULT 'default.png')''')

# Messages Table
c.execute('''CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sender TEXT,
    receiver TEXT,
    group_name TEXT DEFAULT NULL,
    message TEXT DEFAULT NULL,
    attachment TEXT DEFAULT NULL,
    seen INTEGER DEFAULT 0,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')

# Notifications Table
c.execute('''CREATE TABLE IF NOT EXISTS notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user TEXT,
    message TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')

# File Storage Table
c.execute('''CREATE TABLE IF NOT EXISTS files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user TEXT,
    file_name TEXT,
    file_path TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')

conn.commit()
conn.close()
