import asyncio
from app.database import SessionLocal
from app.routers.analytics import get_student_analytics
from fastapi import HTTPException

async def test_endpoint():
    db = SessionLocal()
    try:
        print("Fetching analytics for student 196...")
        result = await get_student_analytics(student_id=196, db=db)
        print("Success! Result keys:", result.keys())
    except HTTPException as e:
        print(f"HTTP Error: {e.status_code} - {e.detail}")
    except Exception as e:
        print(f"Server Error Type: {type(e)}")
        print(f"Server Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(test_endpoint())
