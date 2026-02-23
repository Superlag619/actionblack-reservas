import sqlite3
from datetime import datetime

DB_PATH = "config.db"


def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS config (
            hora_clase TEXT,
            tipo_clase TEXT,
            sede TEXT,
            dias_offset INTEGER,
            updated_at TEXT
        )
        """
    )
    # Si la tabla estaba antes sin dias_offset, la recreamos de forma simple
    c.execute("SELECT COUNT(*) FROM config")
    count = c.fetchone()[0]
    if count == 0:
        # Valores por defecto: 06:00, JAB, Alto de Palmas, reservar mañana (1 día)
        c.execute(
            "INSERT INTO config (hora_clase, tipo_clase, sede, dias_offset, updated_at) "
            "VALUES (?, ?, ?, ?, ?)",
            ("06:00", "JAB", "Alto de Palmas", 1, datetime.now().isoformat()),
        )
    conn.commit()
    conn.close()


def get_config():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute("SELECT hora_clase, tipo_clase, sede, dias_offset FROM config LIMIT 1")
        row = c.fetchone()
    except sqlite3.OperationalError:
        # Por si viene de una versión vieja sin dias_offset
        conn.close()
        init_db()
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT hora_clase, tipo_clase, sede, dias_offset FROM config LIMIT 1")
        row = c.fetchone()

    conn.close()
    if not row:
        return {
            "hora_clase": "06:00",
            "tipo_clase": "JAB",
            "sede": "Alto de Palmas",
            "dias_offset": 1,
        }
    return {
        "hora_clase": row[0],
        "tipo_clase": row[1],
        "sede": row[2],
        "dias_offset": row[3] if row[3] is not None else 1,
    }


def save_config(hora_clase: str, tipo_clase: str, sede: str, dias_offset: int):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM config")
    c.execute(
        "INSERT INTO config (hora_clase, tipo_clase, sede, dias_offset, updated_at) "
        "VALUES (?, ?, ?, ?, ?)",
        (hora_clase, tipo_clase, sede, dias_offset, datetime.now().isoformat()),
    )
    conn.commit()
    conn.close()
