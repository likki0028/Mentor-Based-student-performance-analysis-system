import os
os.environ["DATABASE_URL"] = "postgresql://neondb_owner:npg_vbN1zXRAJ9pr@ep-frosty-bread-a4i9jfpq-pooler.us-east-1.aws.neon.tech/neondb?sslmode=require"

from sqlalchemy import create_engine, text

engine = create_engine(os.environ["DATABASE_URL"])
with engine.connect() as conn:
    tables = conn.execute(text("SELECT tablename FROM pg_tables WHERE schemaname='public'")).fetchall()
    print(f"Tables found: {len(tables)}")
    for t in tables:
        print(f"  - {t[0]}")
    
    if tables:
        for t in tables:
            count = conn.execute(text(f"SELECT COUNT(*) FROM \"{t[0]}\"")).fetchone()[0]
            print(f"  {t[0]}: {count} rows")
    else:
        print("NO TABLES FOUND - database is empty!")
