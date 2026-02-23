import sqlite3
from datetime import datetime

def init_db():
    conn = sqlite3.connect('config.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS config 
                 (hora_clase TEXT, tipo_clase TEXT, sede TEXT, updated_at TEXT)''')
    # Config por defecto
    c.execute("INSERT OR IGNORE INTO config VALUES ('06:00', 'HIIT', 'Cedritos', ?)", 
              (datetime.now().isoformat(),))
    conn.commit()
    conn.close()

def get_config():
    conn = sqlite3.connect('config.db')
    c = conn.cursor()
    c.execute("SELECT * FROM config")
    row = c.fetchone()
    conn.close()
    return {
        'hora_clase': row[0] if row else '06:00',
        'tipo_clase': row[1] if row else 'HIIT', 
        'sede': row[2] if row else 'Cedritos'
    }

def save_config(hora, tipo, sede):
    conn = sqlite3.connect('config.db')
    c = conn.cursor()
    c.execute("UPDATE config SET hora_clase=?, tipo_clase=?, sede=?, updated_at=?",
              (hora, tipo, sede, datetime.now().isoformat()))
    conn.commit()
    conn.close()
