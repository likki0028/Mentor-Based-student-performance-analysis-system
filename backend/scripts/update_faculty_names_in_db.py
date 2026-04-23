import sys
import os
import json

current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)
sys.path.append(backend_dir)

from app.database import SessionLocal
# Import all models to ensure relationships resolve
from app.models import user, student, faculty, subject, section, attendance, marks, alert, assignment, submission, remark, material

def run():
    db = SessionLocal()
    try:
        users = db.query(user.User).filter(user.User.role.in_([user.UserRole.LECTURER, user.UserRole.MENTOR, user.UserRole.BOTH])).all()
        
        target_usernames = {
            "ramasundari": "faculty1",
            "priyanka": "faculty2",
            "kirankumar": "faculty3",
            "ramkumar": "faculty4",
            "lakshmisruthi": "faculty5",
            "sasibhanu": "faculty6",
            "sreevani": "faculty7",
            "manuhajari": "faculty8",
            "saritha_b": "faculty9",
            "tejasvi": "faculty10",
            "swaroopa": "faculty11",
            "mohana": "faculty12",
            "kalpana": "faculty13",
            "srilatha": "faculty14",
            "vsrkraju": "faculty15",
            "mallikarjuna": "faculty16",
            "rashisaxena": "faculty17",
            "niharika": "faculty18",
            "mentor_a": "faculty1",
            "mentor_b": "faculty2",
            "mentor_c": "faculty3",
            "lecturer": "faculty4",
            "mentor": "faculty19",
        }
        
        results = []
        # Check for conflicts first
        existing_names = [u.username for u in users]
        print(f"Found existing faculty usernames: {existing_names}")
        
        for u in users:
            old_name = u.username
            if old_name in target_usernames:
                new_name = target_usernames[old_name]
                
                # Update in DB
                u.username = new_name
                u.email = f"{new_name}@griet.ac.in"
                results.append({"old": old_name, "new": new_name})
                print(f"Updated {old_name} -> {new_name}")
        
        db.commit()
        
        with open(os.path.join(current_dir, "anonymization_results.json"), "w") as f:
            json.dump(results, f, indent=2)
            
        print("Done updating users!")
    except Exception as e:
        db.rollback()
        import traceback
        traceback.print_exc()
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    run()
