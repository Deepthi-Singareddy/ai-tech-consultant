import uvicorn
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.core.config import settings

if __name__ == "__main__":
    print(f"Starting {settings.APP_NAME} on {settings.HOST}:{settings.PORT}")
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=False)
