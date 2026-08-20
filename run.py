import uvicorn
from src.config import config

if __name__ == "__main__":
    print(f"Starting {config.PROJECT_NAME} Server...")
    print("Access Web UI at: http://127.0.0.1:8000")
    print("Access API Docs at: http://127.0.0.1:8000/docs")
    uvicorn.run("src.api.app:app", host="127.0.0.1", port=8000, reload=True)
