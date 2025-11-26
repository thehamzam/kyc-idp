"""Unified database module for users and submissions."""
import sqlite3
import json
import os
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List

DATABASE_PATH = os.getenv('DATABASE_PATH', 'users.db')


@dataclass
class User:
    id: int
    username: str
    password_hash: str
    created_at: datetime

    @classmethod
    def from_row(cls, row: tuple) -> 'User':
        return cls(
            id=row[0],
            username=row[1],
            password_hash=row[2],
            created_at=datetime.fromisoformat(row[3]) if isinstance(row[3], str) else row[3]
        )


@dataclass
class Submission:
    id: int
    user_id: int
    filename: str
    content_type: str
    extraction_data: dict
    created_at: datetime
    image_data: str = None

    @classmethod
    def from_row(cls, row: tuple) -> 'Submission':
        return cls(
            id=row[0],
            user_id=row[1],
            filename=row[2],
            content_type=row[3],
            extraction_data=json.loads(row[4]) if isinstance(row[4], str) else row[4],
            created_at=datetime.fromisoformat(row[5]) if isinstance(row[5], str) else row[5],
            image_data=row[6] if len(row) > 6 else None
        )

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'filename': self.filename,
            'extraction_data': self.extraction_data,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'image_data': self.image_data
        }

    def to_list_item(self) -> dict:
        return {
            'id': self.id,
            'filename': self.filename,
            'document_type': self.extraction_data.get('document_type'),
            'name': self.extraction_data.get('name'),
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


@contextmanager
def get_db():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def init_db():
    """Initialize all database tables."""
    with get_db() as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS submissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                filename TEXT NOT NULL,
                content_type TEXT NOT NULL,
                extraction_data TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                image_data TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_submissions_user ON submissions(user_id)')
        conn.commit()


# User operations
def get_user_by_username(username: str) -> Optional[User]:
    with get_db() as conn:
        row = conn.execute(
            'SELECT id, username, password_hash, created_at FROM users WHERE username = ?',
            (username,)
        ).fetchone()
        return User.from_row(tuple(row)) if row else None


def get_user_by_id(user_id: int) -> Optional[User]:
    with get_db() as conn:
        row = conn.execute(
            'SELECT id, username, password_hash, created_at FROM users WHERE id = ?',
            (user_id,)
        ).fetchone()
        return User.from_row(tuple(row)) if row else None


def create_user(username: str, password_hash: str) -> User:
    with get_db() as conn:
        cursor = conn.execute(
            'INSERT INTO users (username, password_hash) VALUES (?, ?)',
            (username, password_hash)
        )
        conn.commit()
        return get_user_by_id(cursor.lastrowid)


def user_exists(username: str) -> bool:
    with get_db() as conn:
        return conn.execute('SELECT 1 FROM users WHERE username = ?', (username,)).fetchone() is not None


# Submission operations
def create_submission(user_id: int, filename: str, content_type: str, extraction_data: dict, image_data: str = None) -> Submission:
    with get_db() as conn:
        cursor = conn.execute(
            'INSERT INTO submissions (user_id, filename, content_type, extraction_data, image_data) VALUES (?, ?, ?, ?, ?)',
            (user_id, filename, content_type, json.dumps(extraction_data), image_data)
        )
        conn.commit()
        row = conn.execute(
            'SELECT id, user_id, filename, content_type, extraction_data, created_at, image_data FROM submissions WHERE id = ?',
            (cursor.lastrowid,)
        ).fetchone()
        return Submission.from_row(tuple(row))


def get_submissions_by_user(user_id: int) -> List[Submission]:
    with get_db() as conn:
        rows = conn.execute(
            'SELECT id, user_id, filename, content_type, extraction_data, created_at, image_data FROM submissions WHERE user_id = ? ORDER BY created_at DESC',
            (user_id,)
        ).fetchall()
        return [Submission.from_row(tuple(row)) for row in rows]


def get_submission_by_id(submission_id: int, user_id: int) -> Optional[Submission]:
    with get_db() as conn:
        row = conn.execute(
            'SELECT id, user_id, filename, content_type, extraction_data, created_at, image_data FROM submissions WHERE id = ? AND user_id = ?',
            (submission_id, user_id)
        ).fetchone()
        return Submission.from_row(tuple(row)) if row else None


def delete_submission(submission_id: int, user_id: int) -> bool:
    with get_db() as conn:
        cursor = conn.execute('DELETE FROM submissions WHERE id = ? AND user_id = ?', (submission_id, user_id))
        conn.commit()
        return cursor.rowcount > 0
