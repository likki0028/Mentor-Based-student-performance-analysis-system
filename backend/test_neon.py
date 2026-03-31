"""Minimal test: can we insert a single user into Neon?"""
import os
os.environ["DATABASE_URL"] = "postgresql://neondb_owner:npg_5BixMZNfKFO6@ep-muddy-base-a15u2npb-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"

try:
    from app.database import SessionLocal, engine, Base
    from app.models.user import User, UserRole
    from app.core.security import get_password_hash
    
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    # Check if admin already exists
    existing = db.query(User).filter(User.username == "admin").first()
    if existing:
        print(f"Admin already exists with id={existing.id}")
    else:
        admin = User(
            username="admin",
            email="admin@mspa.com",
            hashed_password=get_password_hash("admin123"),
            role=UserRole.ADMIN,
            is_active=True
        )
        db.add(admin)
        db.commit()
        print(f"Admin created with id={admin.id}")
    
    # Count users
    count = db.query(User).count()
    print(f"Total users in DB: {count}")
    db.close()
    print("SUCCESS - Neon connection works!")
    
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
