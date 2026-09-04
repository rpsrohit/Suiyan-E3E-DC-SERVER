import sqlite3
import hashlib
from pathlib import Path
from cryptography.fernet import Fernet
import os
import json

def get_base_dir():
    if "REPLIT" in os.environ:
        return Path("/home")
    elif os.getenv("RAILWAY_VOLUME_MOUNT_PATH"):
        return Path(os.getenv("RAILWAY_VOLUME_MOUNT_PATH"))
    elif os.getenv("RENDER_DISK_NAME"):
        return Path("/opt/render/project/src")
    else:
        return Path.home() / ".telegram_automation_app"

BASE_DIR = get_base_dir()
BASE_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = BASE_DIR / "users.db"
ENCRYPTION_KEY_FILE = BASE_DIR / ".encryption_key"

print(f"→ Using database:     {DB_PATH.absolute()}")
print(f"→ Encryption key at:  {ENCRYPTION_KEY_FILE.absolute()}")
print(f"→ DB exists?         {DB_PATH.exists()}\n")

def get_encryption_key():
    if ENCRYPTION_KEY_FILE.exists():
        with open(ENCRYPTION_KEY_FILE, 'rb') as f:
            return f.read()
    else:
        key = Fernet.generate_key()
        with open(ENCRYPTION_KEY_FILE, 'wb') as f:
            f.write(key)
        return key

ENCRYPTION_KEY = get_encryption_key()
cipher_suite = Fernet(ENCRYPTION_KEY)

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
   
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
   
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_configs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            chat_id TEXT,
            name_prefix TEXT,
            delay INTEGER DEFAULT 30,
            cookies_encrypted TEXT,
            messages TEXT,
            automation_running INTEGER DEFAULT 0,
            locked_group_name TEXT,
            locked_nicknames TEXT,
            lock_enabled INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
   
    for column, definition in [
        ("automation_running", "INTEGER DEFAULT 0"),
        ("locked_group_name", "TEXT"),
        ("locked_nicknames", "TEXT"),
        ("lock_enabled", "INTEGER DEFAULT 0"),
    ]:
        try:
            cursor.execute(f'ALTER TABLE user_configs ADD COLUMN {column} {definition}')
            conn.commit()
        except sqlite3.OperationalError:
            pass
   
    conn.commit()
    conn.close()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def encrypt_cookies(cookies):
    if not cookies:
        return None
    return cipher_suite.encrypt(cookies.encode()).decode()

def decrypt_cookies(encrypted_cookies):
    if not encrypted_cookies:
        return ""
    try:
        return cipher_suite.decrypt(encrypted_cookies.encode()).decode()
    except:
        return ""

def create_user(username, password):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
   
    try:
        password_hash = hash_password(password)
        cursor.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)',
                      (username, password_hash))
        user_id = cursor.lastrowid
       
        cursor.execute('''
            INSERT INTO user_configs (user_id, chat_id, name_prefix, delay, messages)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, '', '', 30, ''))
       
        conn.commit()
        return True, "Account created successfully!"
    except sqlite3.IntegrityError:
        return False, "Username already exists!"
    except Exception as e:
        return False, f"Error: {str(e)}"
    finally:
        conn.close()

def verify_user(username, password):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
   
    try:
        cursor.execute('SELECT id, password_hash FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()
       
        if user and user[1] == hash_password(password):
            return user[0]
        return None
    finally:
        conn.close()

def get_user_config(user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
   
    try:
        cursor.execute('''
            SELECT chat_id, name_prefix, delay, cookies_encrypted, messages, automation_running
            FROM user_configs WHERE user_id = ?
        ''', (user_id,))
       
        config = cursor.fetchone()
       
        if config:
            return {
                'chat_id': config[0] or '',
                'name_prefix': config[1] or '',
                'delay': config[2] or 30,
                'cookies': decrypt_cookies(config[3]),
                'messages': config[4] or '',
                'automation_running': config[5] or 0
            }
        return None
    finally:
        conn.close()

def update_user_config(user_id, chat_id, name_prefix, delay, cookies, messages):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
   
    try:
        encrypted_cookies = encrypt_cookies(cookies)
       
        cursor.execute('''
            UPDATE user_configs
            SET chat_id = ?, name_prefix = ?, delay = ?, cookies_encrypted = ?,
                messages = ?, updated_at = CURRENT_TIMESTAMP
            WHERE user_id = ?
        ''', (chat_id, name_prefix, delay, encrypted_cookies, messages, user_id))
       
        conn.commit()
    finally:
        conn.close()

def get_username(user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
   
    try:
        cursor.execute('SELECT username FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()
        return user[0] if user else None
    finally:
        conn.close()

def set_automation_running(user_id, is_running):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
   
    try:
        cursor.execute('''
            UPDATE user_configs
            SET automation_running = ?, updated_at = CURRENT_TIMESTAMP
            WHERE user_id = ?
        ''', (1 if is_running else 0, user_id))
       
        conn.commit()
    finally:
        conn.close()

def get_automation_running(user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
   
    try:
        cursor.execute('SELECT automation_running FROM user_configs WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        return bool(result[0]) if result else False
    finally:
        conn.close()

def get_lock_config(user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
   
    try:
        cursor.execute('''
            SELECT chat_id, locked_group_name, locked_nicknames, lock_enabled, cookies_encrypted
            FROM user_configs WHERE user_id = ?
        ''', (user_id,))
       
        config = cursor.fetchone()
       
        if config:
            try:
                nicknames = json.loads(config[2]) if config[2] else {}
            except:
                nicknames = {}
           
            return {
                'chat_id': config[0] or '',
                'locked_group_name': config[1] or '',
                'locked_nicknames': nicknames,
                'lock_enabled': bool(config[3]),
                'cookies': decrypt_cookies(config[4])
            }
        return None
    finally:
        conn.close()

def update_lock_config(user_id, chat_id, locked_group_name, locked_nicknames, cookies=None):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
   
    try:
        nicknames_json = json.dumps(locked_nicknames)
       
        if cookies is not None:
            encrypted_cookies = encrypt_cookies(cookies)
            cursor.execute('''
                UPDATE user_configs
                SET chat_id = ?, locked_group_name = ?, locked_nicknames = ?,
                    cookies_encrypted = ?, updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ?
            ''', (chat_id, locked_group_name, nicknames_json, encrypted_cookies, user_id))
        else:
            cursor.execute('''
                UPDATE user_configs
                SET chat_id = ?, locked_group_name = ?, locked_nicknames = ?, updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ?
            ''', (chat_id, locked_group_name, nicknames_json, user_id))
       
        conn.commit()
    finally:
        conn.close()

def set_lock_enabled(user_id, enabled):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
   
    try:
        cursor.execute('''
            UPDATE user_configs
            SET lock_enabled = ?, updated_at = CURRENT_TIMESTAMP
            WHERE user_id = ?
        ''', (1 if enabled else 0, user_id))
       
        conn.commit()
    finally:
        conn.close()

def get_lock_enabled(user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
   
    try:
        cursor.execute('SELECT lock_enabled FROM user_configs WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        return bool(result[0]) if result else False
    finally:
        conn.close()

init_db()
