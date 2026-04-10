import os
import sys
import traceback

PG_URL = "postgresql://neondb_owner:npg_5BixMZNfKFO6@ep-muddy-base-a15u2npb-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"
os.environ["DATABASE_URL"] = PG_URL

from sqlalchemy import create_engine, MetaData, text, Boolean
from app.database import Base, engine as engine_dest
from app.models import user, student, faculty as faculty_model, subject, section
from app.models import remark, material, marks, attendance as att_model
from app.models import assignment, submission, alert, quiz, quiz_attempt
from app.models import quiz_question, quiz_response, assignment_file, material_file
from app.models import extracurricular, doubt, doubt_comment, syllabus_topic
from app.models import mark_finalization, notification, online_meeting

SQLITE_URL = "sqlite:///./sql_app.db"
engine_src = create_engine(SQLITE_URL)
BATCH_SIZE = 500

def fix_row_types(row_dict, table):
    """Convert SQLite integer booleans (0/1) to Python booleans for PostgreSQL."""
    fixed = {}
    for col in table.columns:
        val = row_dict.get(col.name)
        if isinstance(col.type, Boolean) and isinstance(val, int):
            fixed[col.name] = bool(val)
        else:
            fixed[col.name] = val
    return fixed

def migrate():
    print("Step 1: Connecting...")
    meta_src = MetaData()
    meta_src.reflect(bind=engine_src)

    print("Step 2: Dropping all tables on Neon...")
    meta_cleanup = MetaData()
    meta_cleanup.reflect(bind=engine_dest)
    meta_cleanup.drop_all(bind=engine_dest)
    print("  -> Dropped.")

    print("Step 3: Creating fresh schema...")
    Base.metadata.create_all(bind=engine_dest)
    print("  -> Schema created.")

    meta_dest = MetaData()
    meta_dest.reflect(bind=engine_dest)

    print("Step 4: Migrating data...\n")
    
    success_tables = []
    failed_tables = []

    with engine_src.connect() as conn_src:
        for table in meta_dest.sorted_tables:
            src_table = meta_src.tables.get(table.name)
            if src_table is None:
                print(f"  [SKIP]  {table.name}")
                continue

            rows = conn_src.execute(src_table.select()).fetchall()
            if not rows:
                print(f"  [EMPTY] {table.name}")
                continue

            total = len(rows)
            print(f"  [START] {table.name}: {total} rows...")
            data = [fix_row_types(dict(row._mapping), table) for row in rows]

            # Each table gets its own transaction
            try:
                with engine_dest.connect() as conn_dest:
                    for i in range(0, total, BATCH_SIZE):
                        batch = data[i:i + BATCH_SIZE]
                        conn_dest.execute(table.insert(), batch)
                    conn_dest.commit()
                print(f"  [DONE]  {table.name}: {total} rows.")
                success_tables.append(table.name)
            except Exception as e:
                print(f"  [FAIL]  {table.name}: {type(e).__name__}: {str(e)[:200]}")
                failed_tables.append(table.name)

    print("\n" + "=" * 50)
    print(f"Done! Success: {len(success_tables)} tables | Failed: {len(failed_tables)} tables")
    if failed_tables:
        print(f"Failed tables: {failed_tables}")
    else:
        print("MIGRATION COMPLETE! Neon now matches local data.")
    print("=" * 50)

if __name__ == "__main__":
    migrate()
