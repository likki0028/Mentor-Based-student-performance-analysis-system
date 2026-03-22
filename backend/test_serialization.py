"""Run this to test the live endpoint and get precise error"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Must import all models first
from app.models import (
    user, student, faculty, subject, section,
    remark, material, marks, attendance, assignment,
    submission, alert, quiz, quiz_attempt
)
from app.database import SessionLocal
from app.services.analytics_service import AnalyticsService

db = SessionLocal()
try:
    result = AnalyticsService.get_student_analytics(db, 1)
    
    # Now try to JSON serialize it (simulating Pydantic/FastAPI)
    import json
    
    def default_serializer(obj):
        if hasattr(obj, 'value'):
            return obj.value
        if hasattr(obj, '__str__'):
            return str(obj)
        raise TypeError(f"Object of type {type(obj)} not serializable")
    
    try:
        serialized = json.dumps(result, default=default_serializer)
        print("JSON serialization OK, length:", len(serialized))
    except Exception as e:
        print(f"JSON SERIALIZATION ERROR: {e}")
        import traceback
        traceback.print_exc()
        # Find the problematic field
        for key, val in result.items():
            try:
                json.dumps({key: val}, default=default_serializer)
            except Exception as e2:
                print(f"  Field '{key}' failed: {e2}")
                if isinstance(val, list):
                    for i, item in enumerate(val):
                        try:
                            json.dumps(item, default=default_serializer)
                        except Exception as e3:
                            print(f"    Item {i} failed: {e3}")
                            if isinstance(item, dict):
                                for k, v in item.items():
                                    try:
                                        json.dumps({k: v}, default=default_serializer)
                                    except:
                                        print(f"      Sub-field '{k}' = {repr(v)}")
finally:
    db.close()
