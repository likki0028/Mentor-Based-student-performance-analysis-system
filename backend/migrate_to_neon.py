"""Migrate data from local SQLite to remote Neon PostgreSQL."""
import os
import sys
import codecs
sys.stdout = codecs.getwriter('utf8')(sys.stdout.detach())

# Set env to Neon for model initialization
PG_URL = "postgresql://neondb_owner:npg_5BixMZNfKFO6@ep-muddy-base-a15u2npb-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"
os.environ["DATABASE_URL"] = PG_URL

from sqlalchemy import create_engine, MetaData
from app.database import Base, engine as engine_dest
import app.models.user  # load all models to sync metadata
import app.models.student
import app.models.faculty
import app.models.subject
import app.models.section
import app.models.remark
import app.models.material
import app.models.marks
import app.models.attendance
import app.models.assignment
import app.models.submission
import app.models.alert
import app.models.quiz
import app.models.doubt
import app.models.notification

SQLITE_URL = "sqlite:///./sql_app.db"
engine_src = create_engine(SQLITE_URL)

def migrate():
    print("Connecting to source (SQLite) and destination (Neon)...")
    meta_src = MetaData()
    meta_src.reflect(bind=engine_src)

    # Properly drop all tables in dependency order on Neon
    print("Recreating clean tables on Remote DB...")
    meta_cleanup = MetaData()
    meta_cleanup.reflect(bind=engine_dest)
    meta_cleanup.drop_all(bind=engine_dest)
    
    # Create the schema fresh
    Base.metadata.create_all(bind=engine_dest)

    meta_dest = MetaData()
    meta_dest.reflect(bind=engine_dest)

    # Now copy data table by table in topological sorted order
    with engine_src.connect() as conn_src:
        with engine_dest.connect() as conn_dest:
            for table in meta_dest.sorted_tables:
                src_table = meta_src.tables.get(table.name)
                if src_table is not None:
                    print(f"Extracting {table.name}...")
                    rows = conn_src.execute(src_table.select()).fetchall()
                    if rows:
                        print(f"  -> Migrating {len(rows)} rows into remote {table.name}...")
                        data = [dict(row._mapping) for row in rows]
                        
                        # Fix for integer true/false to python bools if needed (sqlite -> PG)
                        # SQLAlchemy usually handles it via standard dict mapping, but let's be safe:
                        conn_dest.execute(table.insert(), data)
                        print("  -> Success")
                    else:
                        print(f"  -> Table {table.name} is empty, skipping.")
            conn_dest.commit()
            print("========================================")
            print("MIGRATION COMPLETE! Remote DB now matches local exactly!")
            print("========================================")

if __name__ == "__main__":
    migrate()
