import os

import uvicorn

try:
    # Import path when the backend package is loaded from project root.
    from backend.app.main import app
except ModuleNotFoundError:
    # Import path when running from inside the backend directory.
    from app.main import app


if __name__ == "__main__":
    port = int(os.getenv("PORT", 3001))
    target = "backend.app.main:app" if __package__ == "backend" else "app.main:app"
    uvicorn.run(target, host="0.0.0.0", port=port, reload=True)

