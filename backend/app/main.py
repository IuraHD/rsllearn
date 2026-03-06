import os
import traceback

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .api.routers import admin, ai, auth, lessons, user
from .core.config import BACKEND_DIR, CORS_ORIGINS
from .db.database import Base, engine


# Ensure schema exists
Base.metadata.create_all(bind=engine)

app = FastAPI(title="RSLlingo API", description="Python FastAPI Backend for RSLlingo")


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    error_msg = traceback.format_exc()
    (BACKEND_DIR / "global_error.txt").write_text(error_msg, encoding="utf-8")
    print(f"Global error: {error_msg}")
    return JSONResponse(
        status_code=500,
        content={"message": "Internal Server Error", "detail": str(exc)},
    )


app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
app.include_router(user.router, prefix="/api/user", tags=["User"])
app.include_router(lessons.router, prefix="/api/lessons", tags=["Lessons"])
app.include_router(ai.router, prefix="/api", tags=["AI"])
app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])


@app.get("/api/health")
def health_check():
    return {
        "success": True,
        "message": "RSLlingo API is running (Python/FastAPI)",
        "timestamp": "2024-01-15T10:30:00.000Z",
    }


if __name__ == "__main__":
    port = int(os.getenv("PORT", 3001))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True)
