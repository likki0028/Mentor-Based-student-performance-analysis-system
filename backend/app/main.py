
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .routers import alerts, quizzes, students, faculty, attendance, assignments, analytics, auth, marks_router, materials, doubts, syllabus, exports, notifications
from .admin import admin_router
from .database import engine, Base
# Ensure all models are registered with the mapper before create_all
from .models import user, student, faculty as faculty_model, subject, section  # noqa
from .models import remark, material, marks, attendance as att_model  # noqa
from .models import assignment, submission, alert, quiz, quiz_attempt, quiz_question, quiz_response, assignment_file, material_file  # noqa
from .models import doubt, doubt_comment, syllabus_topic, mark_finalization  # noqa
from .models import notification  # noqa
from .scheduler.scheduler import start_scheduler
import logging

logger = logging.getLogger(__name__)

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Custom handler that safely serializes validation errors without crashing on binary data."""
    errors = []
    for error in exc.errors():
        safe_error = {
            "type": error.get("type", ""),
            "loc": [str(l) for l in error.get("loc", [])],
            "msg": error.get("msg", ""),
        }
        errors.append(safe_error)
    return JSONResponse(status_code=422, content={"detail": errors})

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Global exception caught: {exc}")
    # Manually add CORS headers to the error response to avoid CORS blocks on frontend
    headers = {
        "Access-Control-Allow-Origin": request.headers.get("origin", "*"),
        "Access-Control-Allow-Credentials": "true",
        "Access-Control-Allow-Methods": "*",
        "Access-Control-Allow-Headers": "*"
    }
    return JSONResponse(
        status_code=500,
        content={"message": "Internal Server Error", "details": str(exc)},
        headers=headers
    )


# CORS Middleware — allow all origins for deployment flexibility
import os
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5174",
    "http://localhost:5175",
    "http://localhost:5176",
    "http://localhost:5177",
    "http://localhost:5178",
    "http://localhost:5179",
    "http://localhost:5180",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://mentor-based-student-performance-an.vercel.app",
]
# Add FRONTEND_URL from env if provided
frontend_url = os.environ.get("FRONTEND_URL")
if frontend_url:
    origins.append(frontend_url)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for free-tier deployment
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    try:
        start_scheduler()
        logger.info("Background scheduler started — alerts will auto-generate every 24h")
    except Exception as e:
        logger.warning(f"Scheduler failed to start: {e}")

@app.get("/")
def read_root():
    return {"message": "Welcome to Mentor-Based Student Performance System API"}

# Include routers
app.include_router(auth.router)
app.include_router(alerts.router, prefix="/alerts", tags=["alerts"])
app.include_router(quizzes.router, prefix="/quizzes", tags=["quizzes"])
app.include_router(students.router, prefix="/students", tags=["students"])
app.include_router(faculty.router, prefix="/faculty", tags=["faculty"])
app.include_router(attendance.router, prefix="/attendance", tags=["attendance"])
app.include_router(assignments.router, prefix="/assignments", tags=["assignments"])
app.include_router(materials.router, prefix="/materials", tags=["materials"])
app.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
app.include_router(marks_router.router, prefix="/marks", tags=["marks"])
app.include_router(admin_router.router, prefix="/admin", tags=["admin"])
app.include_router(doubts.router, prefix="/doubts", tags=["doubts"])
app.include_router(syllabus.router, prefix="/syllabus", tags=["syllabus"])
app.include_router(exports.router, prefix="/exports", tags=["exports"])
app.include_router(notifications.router, prefix="/notifications", tags=["notifications"])

# Serve uploaded files (assignments, submissions) as static files
from fastapi.staticfiles import StaticFiles
import os
uploads_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
os.makedirs(uploads_dir, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=uploads_dir), name="uploads")
