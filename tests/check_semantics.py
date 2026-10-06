import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

from src.database import get_connection


conn = get_connection()
cursor = conn.cursor()

cursor.execute("""
    SELECT
        portrait_framing,
        COUNT(*)
    FROM photo_semantics
    GROUP BY portrait_framing
""")

for row in cursor.fetchall():
    print(
        row["portrait_framing"],
        row[1]
    )

conn.close()