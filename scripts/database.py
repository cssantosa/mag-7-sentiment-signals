import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS sentiment_scores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    posted_at TEXT,
    fetched_at TEXT,
    headline TEXT NOT NULL,
    url TEXT NOT NULL,
    source TEXT,
    reporter TEXT,
    ticker TEXT NOT NULL,
    is_ai_related INTEGER,
    is_proxy_partnership INTEGER,
    sentiment_vader REAL,
    sentiment_llm_phi3 REAL,
    sentiment_llm_llama3_2 REAL,
    sentiment_llm_deepseek_r1 REAL,
    UNIQUE(headline, url, ticker)
);
"""


def get_db_path() -> Path:
    """Return path to data/sentiment.db; ensure data/ exists."""
    data_dir = ROOT / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir / "sentiment.db"


def get_connection() -> sqlite3.Connection:
    """Open and return a connection to the sentiment DB. Caller must close."""
    return sqlite3.connect(get_db_path())


def init_db(conn: sqlite3.Connection) -> None:
    """Create sentiment_scores table if it does not exist."""
    conn.execute(CREATE_TABLE)
    conn.commit()


def _row_to_tuple(row: dict) -> tuple:
    """Map a processed row dict to (posted_at, fetched_at, ..., sentiment_llm_deepseek_r1)."""
    def b(v):
        return 1 if v is True else (0 if v is False else None)
    return (
        row.get("posted_at"),
        row.get("fetched_at"),
        row.get("headline") or "",
        row.get("url") or "",
        row.get("source"),
        row.get("reporter"),
        row.get("ticker") or "",
        b(row.get("is_ai_related")),
        b(row.get("is_proxy_partnership")),
        row.get("sentiment_vader"),
        row.get("sentiment_llm_phi3"),
        row.get("sentiment_llm_llama3_2"),
        row.get("sentiment_llm_deepseek_r1"),
    )


def insert_processed_rows(conn: sqlite3.Connection, rows: list[dict]) -> int:
    """
    Insert processed rows into sentiment_scores. Uses INSERT OR IGNORE so
    duplicate (headline, url, ticker) are skipped. Calls init_db(conn) first.
    Returns number of rows inserted.
    """
    init_db(conn)
    if not rows:
        return 0
    cols = (
        "posted_at", "fetched_at", "headline", "url", "source", "reporter",
        "ticker", "is_ai_related", "is_proxy_partnership",
        "sentiment_vader", "sentiment_llm_phi3", "sentiment_llm_llama3_2", "sentiment_llm_deepseek_r1",
    )
    placeholders = ", ".join("?" for _ in cols)
    sql = f"INSERT OR IGNORE INTO sentiment_scores ({', '.join(cols)}) VALUES ({placeholders})"
    cursor = conn.cursor()
    count_before = cursor.execute("SELECT COUNT(*) FROM sentiment_scores").fetchone()[0]
    for row in rows:
        cursor.execute(sql, _row_to_tuple(row))
    conn.commit()
    count_after = cursor.execute("SELECT COUNT(*) FROM sentiment_scores").fetchone()[0]
    return count_after - count_before


if __name__ == "__main__":
    conn = get_connection()
    try:
        init_db(conn)
        print(f"DB initialized: {get_db_path()}")
    finally:
        conn.close()
