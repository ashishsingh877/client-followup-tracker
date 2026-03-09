import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "client_tracker.db")


def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS clients (
            client_id        INTEGER PRIMARY KEY AUTOINCREMENT,
            client_name      TEXT NOT NULL,
            email            TEXT,
            phone            TEXT,
            engagement_type  TEXT,
            estimated_fee    REAL,
            client_status    TEXT DEFAULT 'Active',
            engagement_stage TEXT DEFAULT 'Lead Identified',
            created_date     TEXT DEFAULT (datetime('now'))
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS engagement_stages (
            id                        INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id                 INTEGER UNIQUE,
            questionnaire_sent_date   TEXT,
            approach_note_sent_date   TEXT,
            proposal_sent_date        TEXT,
            FOREIGN KEY (client_id) REFERENCES clients(client_id)
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS notes (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id           INTEGER UNIQUE,
            current_stage_notes TEXT,
            next_step_notes     TEXT,
            FOREIGN KEY (client_id) REFERENCES clients(client_id)
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS followups (
            followup_id       INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id         INTEGER,
            task_description  TEXT,
            followup_datetime TEXT,
            status            TEXT DEFAULT 'Pending',
            reminder_count    INTEGER DEFAULT 0,
            last_shown_time   TEXT,
            completed_time    TEXT,
            FOREIGN KEY (client_id) REFERENCES clients(client_id)
        )
    """)

    conn.commit()
    conn.close()


# ─── CLIENTS ────────────────────────────────────────────────────────────────

def add_client(name, email, phone, eng_type, fee, status, stage):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        INSERT INTO clients (client_name, email, phone, engagement_type,
                             estimated_fee, client_status, engagement_stage)
        VALUES (?,?,?,?,?,?,?)
    """, (name, email, phone, eng_type, fee, status, stage))
    client_id = c.lastrowid
    c.execute("INSERT OR IGNORE INTO engagement_stages (client_id) VALUES (?)", (client_id,))
    c.execute("INSERT OR IGNORE INTO notes (client_id) VALUES (?)", (client_id,))
    conn.commit()
    conn.close()
    return client_id


def update_client(client_id, name, email, phone, eng_type, fee, status, stage):
    conn = get_conn()
    conn.execute("""
        UPDATE clients SET client_name=?, email=?, phone=?, engagement_type=?,
            estimated_fee=?, client_status=?, engagement_stage=?
        WHERE client_id=?
    """, (name, email, phone, eng_type, fee, status, stage, client_id))
    conn.commit()
    conn.close()


def delete_client(client_id):
    conn = get_conn()
    conn.execute("DELETE FROM followups WHERE client_id=?", (client_id,))
    conn.execute("DELETE FROM engagement_stages WHERE client_id=?", (client_id,))
    conn.execute("DELETE FROM notes WHERE client_id=?", (client_id,))
    conn.execute("DELETE FROM clients WHERE client_id=?", (client_id,))
    conn.commit()
    conn.close()


def get_all_clients():
    conn = get_conn()
    rows = conn.execute("""
        SELECT c.*, es.questionnaire_sent_date, es.approach_note_sent_date,
               es.proposal_sent_date, n.current_stage_notes, n.next_step_notes
        FROM clients c
        LEFT JOIN engagement_stages es ON c.client_id = es.client_id
        LEFT JOIN notes n ON c.client_id = n.client_id
        ORDER BY c.created_date DESC
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_client(client_id):
    conn = get_conn()
    row = conn.execute("""
        SELECT c.*, es.questionnaire_sent_date, es.approach_note_sent_date,
               es.proposal_sent_date, n.current_stage_notes, n.next_step_notes
        FROM clients c
        LEFT JOIN engagement_stages es ON c.client_id = es.client_id
        LEFT JOIN notes n ON c.client_id = n.client_id
        WHERE c.client_id=?
    """, (client_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def search_clients(query):
    conn = get_conn()
    rows = conn.execute("""
        SELECT c.*, es.questionnaire_sent_date, es.approach_note_sent_date,
               es.proposal_sent_date, n.current_stage_notes, n.next_step_notes
        FROM clients c
        LEFT JOIN engagement_stages es ON c.client_id = es.client_id
        LEFT JOIN notes n ON c.client_id = n.client_id
        WHERE c.client_name LIKE ? OR c.email LIKE ? OR c.phone LIKE ?
        ORDER BY c.created_date DESC
    """, (f"%{query}%", f"%{query}%", f"%{query}%")).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ─── ENGAGEMENT STAGES ──────────────────────────────────────────────────────

def update_engagement_dates(client_id, q_date, approach_date, proposal_date):
    conn = get_conn()
    conn.execute("""
        INSERT INTO engagement_stages (client_id, questionnaire_sent_date,
            approach_note_sent_date, proposal_sent_date)
        VALUES (?,?,?,?)
        ON CONFLICT(client_id) DO UPDATE SET
            questionnaire_sent_date=excluded.questionnaire_sent_date,
            approach_note_sent_date=excluded.approach_note_sent_date,
            proposal_sent_date=excluded.proposal_sent_date
    """, (client_id, q_date, approach_date, proposal_date))
    conn.commit()
    conn.close()


# ─── NOTES ──────────────────────────────────────────────────────────────────

def update_notes(client_id, current_notes, next_step_notes):
    conn = get_conn()
    conn.execute("""
        INSERT INTO notes (client_id, current_stage_notes, next_step_notes)
        VALUES (?,?,?)
        ON CONFLICT(client_id) DO UPDATE SET
            current_stage_notes=excluded.current_stage_notes,
            next_step_notes=excluded.next_step_notes
    """, (client_id, current_notes, next_step_notes))
    conn.commit()
    conn.close()


# ─── FOLLOW-UPS ─────────────────────────────────────────────────────────────

def add_followup(client_id, task, followup_datetime):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        INSERT INTO followups (client_id, task_description, followup_datetime)
        VALUES (?,?,?)
    """, (client_id, task, followup_datetime))
    fid = c.lastrowid
    conn.commit()
    conn.close()
    return fid


def get_followups(client_id=None):
    conn = get_conn()
    if client_id:
        rows = conn.execute("""
            SELECT f.*, c.client_name FROM followups f
            JOIN clients c ON f.client_id = c.client_id
            WHERE f.client_id=?
            ORDER BY f.followup_datetime
        """, (client_id,)).fetchall()
    else:
        rows = conn.execute("""
            SELECT f.*, c.client_name FROM followups f
            JOIN clients c ON f.client_id = c.client_id
            ORDER BY f.followup_datetime
        """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_due_followups():
    """Return followups due now and not shown within last 1 hour."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    conn = get_conn()
    rows = conn.execute("""
        SELECT f.*, c.client_name FROM followups f
        JOIN clients c ON f.client_id = c.client_id
        WHERE f.status = 'Pending'
          AND f.followup_datetime <= ?
          AND (f.last_shown_time IS NULL
               OR (strftime('%s','now') - strftime('%s', f.last_shown_time)) >= 3600)
        ORDER BY f.followup_datetime
    """, (now,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def mark_followup_shown(followup_id):
    conn = get_conn()
    conn.execute("""
        UPDATE followups SET
            last_shown_time = datetime('now'),
            reminder_count  = reminder_count + 1
        WHERE followup_id=?
    """, (followup_id,))
    conn.commit()
    conn.close()


def complete_followup(followup_id):
    conn = get_conn()
    conn.execute("""
        UPDATE followups SET status='Completed', completed_time=datetime('now')
        WHERE followup_id=?
    """, (followup_id,))
    conn.commit()
    conn.close()


def reschedule_followup(followup_id, new_datetime):
    conn = get_conn()
    conn.execute("""
        UPDATE followups SET followup_datetime=?, status='Pending',
            last_shown_time=NULL, reminder_count=0
        WHERE followup_id=?
    """, (new_datetime, followup_id))
    conn.commit()
    conn.close()


def delete_followup(followup_id):
    conn = get_conn()
    conn.execute("DELETE FROM followups WHERE followup_id=?", (followup_id,))
    conn.commit()
    conn.close()


# ─── DASHBOARD STATS ────────────────────────────────────────────────────────

def get_dashboard_stats():
    conn = get_conn()
    total        = conn.execute("SELECT COUNT(*) FROM clients").fetchone()[0]
    active       = conn.execute("SELECT COUNT(*) FROM clients WHERE client_status='Active'").fetchone()[0]
    pending_fu   = conn.execute("SELECT COUNT(*) FROM followups WHERE status='Pending'").fetchone()[0]
    overdue      = conn.execute("""
        SELECT COUNT(*) FROM followups
        WHERE status='Pending' AND followup_datetime < datetime('now')
    """).fetchone()[0]
    won          = conn.execute("SELECT COUNT(*) FROM clients WHERE engagement_stage='Won'").fetchone()[0]
    stage_dist   = conn.execute("""
        SELECT engagement_stage, COUNT(*) as cnt FROM clients GROUP BY engagement_stage
    """).fetchall()
    total_fees   = conn.execute(
        "SELECT SUM(estimated_fee) FROM clients WHERE client_status='Active'"
    ).fetchone()[0] or 0
    conn.close()
    return {
        "total_clients":     total,
        "active_clients":    active,
        "pending_followups": pending_fu,
        "overdue_followups": overdue,
        "won_clients":       won,
        "stage_distribution": [dict(r) for r in stage_dist],
        "total_fees":        total_fees,
    }
