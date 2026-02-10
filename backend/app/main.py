
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .routers import alerts, quizzes, students, faculty, attendance, assignments, analytics
from .auth import auth_router
from .admin import admin_router
from .database import engine, Base

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Global Exception Handlers
from fastapi import Request
from fastapi.responses import JSONResponse

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"message": "Internal Server Error", "details": str(exc)},
    )


# CORS Middleware
origins = [
    "http://localhost:5173",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Welcome to Mentor-Based Student Performance System API"}

# Include routers
app.include_router(auth_router.router, prefix="/auth", tags=["auth"])
app.include_router(alerts.router, prefix="/alerts", tags=["alerts"])
app.include_router(quizzes.router, prefix="/quizzes", tags=["quizzes"])
app.include_router(students.router, prefix="/students", tags=["students"])
app.include_router(faculty.router, prefix="/faculty", tags=["faculty"])
app.include_router(attendance.router, prefix="/attendance", tags=["attendance"])
app.include_router(assignments.router, prefix="/assignments", tags=["assignments"])
app.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
app.include_router(admin_router.router, prefix="/admin", tags=["admin"])
