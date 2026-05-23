import uvicorn
from app.database import engine, Base
from app import models

print("Creating database tables...")
Base.metadata.create_all(bind=engine)

print("Starting server...")
print("Open http://127.0.0.1:8000/docs in your browser")

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
