import os
import sqlalchemy as sa
from sqlalchemy import text
from datetime import datetime
import streamlit as st

DB_HOST = st.secrets["DB_HOST"]
DB_NAME = st.secrets["DB_NAME"]
DB_USER = st.secrets["DB_USER"]
DB_PASS = st.secrets["DB_PASS"]
DB_PORT = st.secrets["DB_PORT"]

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}?sslmode=require"
engine = sa.create_engine(DATABASE_URL, pool_pre_ping=True)


def get_conn():
    return engine.connect()


def init_db():
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS clients (
                client_id        SERIAL PRIMARY KEY,
                client_name      TEXT NOT NULL,
                email            TEXT,
                phone            TEXT,
                engagement_type  TEXT,
                estimated_fee    NUMERIC,
                client_status    TEXT DEFAULT 'Active',
                engagement_stage TEXT DEFAULT 'Lead Identified',
                created_date     TIMESTAMP DEFAULT NOW()
            )
        """))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS engagement_stages (
                id                        SERIAL PRIMARY KEY,
                client_id                 INTEGER UNIQUE,
                questionnaire_sent_date   TEXT,
                approach_note_sent_date   TEXT,
                proposal_sent_date        TEXT
            )
        """))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS notes (
                id                  SERIAL PRIMARY KEY,
                client_id           INTEGER UNIQUE,
                current_stage_notes TEXT,
                next_step_notes     TEXT
            )
        """))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS followups (
                followup_id       SERIAL PRIMARY KEY,
                client_id         INTEGER,
                task_description  TEXT,
                followup_datetime TEXT,
                status            TEXT DEFAULT 'Pending',
                reminder_count    INTEGER DEFAULT 0,
                last_shown_time   TEXT,
                completed_time    TEXT
            )
        """))


# ─── CLIENTS ────────────────────────────────────────────────────────────────

def add_client(name, email, phone, eng_type, fee, status, stage):
    with engine.begin() as conn:
        result = conn.execute(text("""
            INSERT INTO clients (client_name, email, phone, engagement_type,
                                 estimated_fee, client_status, engagement_stage)
            VALUES (:n,:e,:p,:et,:f,:s,:st)
            RETURNING client_id
        """), dict(n=name, e=email, p=phone, et=eng_type, f=fee, s=status, st=stage))
        client_id = result.fetchone()[0]
        conn.execute(text("""
            INSERT INTO engagement_stages (client_id)
            VALUES (:cid) ON CONFLICT DO NOTHING
        """), dict(cid=client_id))
        conn.execute(text("""
            INSERT INTO notes (client_id)
            VALUES (:cid) ON CONFLICT DO NOTHING
        """), dict(cid=client_id))
    return client_id


def update_client(client_id, name, email, phone, eng_type, fee, status, stage):
    with engine.begin() as conn:
        conn.execute(text("""
            UPDATE clients SET client_name=:n, email=:e, phone=:p,
                engagement_type=:et, estimated_fee=:f,
                client_status=:s, engagement_stage=:st
            WHERE client_id=:cid
        """), dict(n=name, e=email, p=phone, et=eng_type, f=fee,
                   s=status, st=stage, cid=client_id))


def delete_client(client_id):
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM followups WHERE client_id=:c"), dict(c=client_id))
        conn.execute(text("DELETE FROM engagement_stages WHERE client_id=:c"), dict(c=client_id))
        conn.execute(text("DELETE FROM notes WHERE client_id=:c"), dict(c=client_id))
        conn.execute(text("DELETE FROM clients WHERE client_id=:c"), dict(c=client_id))


def get_all_clients():
    with engine.connect() as conn:
        rows = conn.execute(text("""
            SELECT c.*, es.questionnaire_sent_date, es.approach_note_sent_date,
                   es.proposal_sent_date, n.current_stage_notes, n.next_step_notes
            FROM clients c
            LEFT JOIN engagement_stages es ON c.client_id = es.client_id
            LEFT JOIN notes n ON c.client_id = n.client_id
            ORDER BY c.created_date DESC
        """)).fetchall()
    return [dict(r._mapping) for r in rows]


def get_client(client_id):
    with engine.connect() as conn:
        row = conn.execute(text("""
            SELECT c.*, es.questionnaire_sent_date, es.approach_note_sent_date,
                   es.proposal_sent_date, n.current_stage_notes, n.next_step_notes
            FROM clients c
            LEFT JOIN engagement_stages es ON c.client_id = es.client_id
            LEFT JOIN notes n ON c.client_id = n.client_id
            WHERE c.client_id=:cid
        """), dict(cid=client_id)).fetchone()
    return dict(row._mapping) if row else None


def search_clients(query):
    with engine.connect() as conn:
        rows = conn.execute(text("""
            SELECT c.*, es.questionnaire_sent_date, es.approach_note_sent_date,
                   es.proposal_sent_date, n.current_stage_notes, n.next_step_notes
            FROM clients c
            LEFT JOIN engagement_stages es ON c.client_id = es.client_id
            LEFT JOIN notes n ON c.client_id = n.client_id
            WHERE c.client_name ILIKE :q OR c.email ILIKE :q OR c.phone ILIKE :q
            ORDER BY c.created_date DESC
        """), dict(q=f"%{query}%")).fetchall()
    return [dict(r._mapping) for r in rows]


# ─── ENGAGEMENT STAGES ──────────────────────────────────────────────────────

def update_engagement_dates(client_id, q_date, approach_date, proposal_date):
    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO engagement_stages
                (client_id, questionnaire_sent_date, approach_note_sent_date, proposal_sent_date)
            VALUES (:cid,:q,:a,:p)
            ON CONFLICT (client_id) DO UPDATE SET
                questionnaire_sent_date=EXCLUDED.questionnaire_sent_date,
                approach_note_sent_date=EXCLUDED.approach_note_sent_date,
                proposal_sent_date=EXCLUDED.proposal_sent_date
        """), dict(cid=client_id, q=q_date, a=approach_date, p=proposal_date))


# ─── NOTES ──────────────────────────────────────────────────────────────────

def update_notes(client_id, current_notes, next_step_notes):
    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO notes (client_id, current_stage_notes, next_step_notes)
            VALUES (:cid,:cn,:nn)
            ON CONFLICT (client_id) DO UPDATE SET
                current_stage_notes=EXCLUDED.current_stage_notes,
                next_step_notes=EXCLUDED.next_step_notes
        """), dict(cid=client_id, cn=current_notes, nn=next_step_notes))


# ─── FOLLOW-UPS ─────────────────────────────────────────────────────────────

def add_followup(client_id, task, followup_datetime):
    with engine.begin() as conn:
        result = conn.execute(text("""
            INSERT INTO followups (client_id, task_description, followup_datetime)
            VALUES (:c,:t,:dt) RETURNING followup_id
        """), dict(c=client_id, t=task, dt=followup_datetime))
        return result.fetchone()[0]


def get_followups(client_id=None):
    with engine.connect() as conn:
        if client_id:
            rows = conn.execute(text("""
                SELECT f.*, c.client_name FROM followups f
                JOIN clients c ON f.client_id = c.client_id
                WHERE f.client_id=:cid ORDER BY f.followup_datetime
            """), dict(cid=client_id)).fetchall()
        else:
            rows = conn.execute(text("""
                SELECT f.*, c.client_name FROM followups f
                JOIN clients c ON f.client_id = c.client_id
                ORDER BY f.followup_datetime
            """)).fetchall()
    return [dict(r._mapping) for r in rows]


def get_due_followups():
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    with engine.connect() as conn:
        rows = conn.execute(text("""
            SELECT f.*, c.client_name FROM followups f
            JOIN clients c ON f.client_id = c.client_id
            WHERE f.status = 'Pending'
              AND f.followup_datetime <= :now
              AND (f.last_shown_time IS NULL
                   OR EXTRACT(EPOCH FROM (NOW() - f.last_shown_time::timestamp)) >= 3600)
            ORDER BY f.followup_datetime
        """), dict(now=now)).fetchall()
    return [dict(r._mapping) for r in rows]


def mark_followup_shown(followup_id):
    with engine.begin() as conn:
        conn.execute(text("""
            UPDATE followups SET
                last_shown_time = NOW()::text,
                reminder_count  = reminder_count + 1
            WHERE followup_id=:fid
        """), dict(fid=followup_id))


def complete_followup(followup_id):
    with engine.begin() as conn:
        conn.execute(text("""
            UPDATE followups SET status='Completed', completed_time=NOW()::text
            WHERE followup_id=:fid
        """), dict(fid=followup_id))


def reschedule_followup(followup_id, new_datetime):
    with engine.begin() as conn:
        conn.execute(text("""
            UPDATE followups SET followup_datetime=:dt, status='Pending',
                last_shown_time=NULL, reminder_count=0
            WHERE followup_id=:fid
        """), dict(dt=new_datetime, fid=followup_id))


def delete_followup(followup_id):
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM followups WHERE followup_id=:fid"),
                     dict(fid=followup_id))


# ─── DASHBOARD STATS ────────────────────────────────────────────────────────

def get_dashboard_stats():
    with engine.connect() as conn:
        total      = conn.execute(text("SELECT COUNT(*) FROM clients")).scalar()
        active     = conn.execute(text("SELECT COUNT(*) FROM clients WHERE client_status='Active'")).scalar()
        pending_fu = conn.execute(text("SELECT COUNT(*) FROM followups WHERE status='Pending'")).scalar()
        overdue    = conn.execute(text("""
            SELECT COUNT(*) FROM followups
            WHERE status='Pending' AND followup_datetime < NOW()::text
        """)).scalar()
        won        = conn.execute(text("SELECT COUNT(*) FROM clients WHERE engagement_stage='Won'")).scalar()
        stage_dist = conn.execute(text("""
            SELECT engagement_stage, COUNT(*) as cnt FROM clients GROUP BY engagement_stage
        """)).fetchall()
        total_fees = conn.execute(text(
            "SELECT SUM(estimated_fee) FROM clients WHERE client_status='Active'"
        )).scalar() or 0
    return {
        "total_clients":      total,
        "active_clients":     active,
        "pending_followups":  pending_fu,
        "overdue_followups":  overdue,
        "won_clients":        won,
        "stage_distribution": [dict(r._mapping) for r in stage_dist],
        "total_fees":         total_fees,
    }
