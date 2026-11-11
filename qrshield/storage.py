import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / 'qrshield.db'

SCHEMA = """
CREATE TABLE IF NOT EXISTS scans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scanned_at TEXT NOT NULL,
    url TEXT NOT NULL,
    host TEXT NOT NULL,
    verdict TEXT NOT NULL,
    risk REAL,
    source TEXT NOT NULL,
    reasons TEXT
);
CREATE TABLE IF NOT EXISTS allowlist (host TEXT PRIMARY KEY, added_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS blocklist (host TEXT PRIMARY KEY, added_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scan_id INTEGER NOT NULL REFERENCES scans(id),
    correct_label TEXT NOT NULL,
    created_at TEXT NOT NULL
);
"""

DEFAULT_ALLOW = ['google.com', 'youtube.com', 'gmail.com', 'microsoft.com', 'apple.com', 'icloud.com', 'amazon.com',
                 'paypal.com', 'netflix.com', 'facebook.com', 'instagram.com', 'whatsapp.com', 'linkedin.com',
                 'github.com', 'wikipedia.org', 'chase.com', 'bankofamerica.com', 'wellsfargo.com', 'usps.com',
                 'fedex.com', 'ups.com', 'irs.gov', 'rowan.edu']


def now():
    return datetime.now().isoformat(timespec='seconds')


def connect(path=DB_PATH):
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.executescript(SCHEMA)
    if conn.execute('SELECT COUNT(*) FROM allowlist').fetchone()[0] == 0:
        conn.executemany('INSERT INTO allowlist VALUES (?, ?)', [(h, now()) for h in DEFAULT_ALLOW])
    conn.commit()
    return conn


def _matches(conn, table, host, include_parents):
    hosts = [host]
    if include_parents:
        hosts += ['.'.join(host.split('.')[i:]) for i in range(1, host.count('.'))]
    marks = ','.join('?' * len(hosts))
    return conn.execute(f'SELECT 1 FROM {table} WHERE host IN ({marks})', hosts).fetchone() is not None


def lookup(conn, host):
    if _matches(conn, 'blocklist', host, include_parents=True):
        return 'PHISHING'
    if _matches(conn, 'allowlist', host, include_parents=False):
        return 'SAFE'
    return None


def add_host(conn, table, host):
    conn.execute(f'INSERT OR REPLACE INTO {table} VALUES (?, ?)', (host, now()))
    conn.commit()


def log_scan(conn, result, source):
    cur = conn.execute(
        'INSERT INTO scans (scanned_at, url, host, verdict, risk, source, reasons) VALUES (?, ?, ?, ?, ?, ?, ?)',
        (now(), result['url'], result['host'], result['verdict'], result['risk'], source, '; '.join(result['reasons'])))
    conn.commit()
    return cur.lastrowid


def add_feedback(conn, scan_id, correct_label):
    conn.execute('INSERT INTO feedback (scan_id, correct_label, created_at) VALUES (?, ?, ?)', (scan_id, correct_label, now()))
    conn.commit()


def recent_scans(conn, limit=20):
    return conn.execute(
        'SELECT scanned_at, host, verdict, ROUND(risk, 3), source FROM scans ORDER BY id DESC LIMIT ?', (limit,)).fetchall()
