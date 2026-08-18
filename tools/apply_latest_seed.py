import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from backend.app.master_seed import seed_verified_master

database = Path("data/processed/sebatik.db")
connection = sqlite3.connect(database)
columns = {row[1] for row in connection.execute("PRAGMA table_info(usulan_nilai)")}
if "periode" not in columns:
    connection.execute("ALTER TABLE usulan_nilai ADD COLUMN periode INTEGER")
connection.commit()
connection.close()
seed_verified_master(database)
print("migrasi periode dan seed selesai")
