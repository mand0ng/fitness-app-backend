import os, requests, json
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi import HTTPException

from config.my_logger import get_logger
from config.env_vars import load_config

# Route imports
from routes.users import userRoutes
from routes.authentticate import authRoutes
from routes.workouts import workoutRoutes

load_config()
logger = get_logger(__name__, "main")

N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL")
DATABASE_URL = os.getenv("DATABASE_URL")
FRONTEND_URL = os.getenv("FRONTEND_URL")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL],  # Frontend origin
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods 
    allow_headers=["*"],  # Allow all headers
)

# Include routes here
app.include_router(userRoutes)
app.include_router(authRoutes)
app.include_router(workoutRoutes)

# TEST ENDPOINTS
@app.get("/hello-world")
def read_root():
    return {"message": "Hello World"}

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/env")
def environment_check():
    return {
        "ENVIRONMENT": os.getenv("ENVIRONMENT"),
        "MANDONG_HELLO": os.getenv("MANDONG_HELLO"),
        "ENV_ENVIRONMENT": os.getenv("ENV_ENVIRONMENT"),
        "FRONTEND_URL" : FRONTEND_URL
    }

@app.get("/call-n8n-sync")
def call_n8n_webhook_sync():
    """
    Synchronous version - GET request to n8n webhook
    """
    try:
        # Since your curl GET request works, use GET with data in query params or body
        response = requests.get(
            N8N_WEBHOOK_URL,
            json={},  # or use data={} if n8n expects form data
            timeout=30,
            headers={"Content-Type": "application/json"}
        )
        
        # Debug information
        print(f"Response status: {response.status_code}")
        print(f"Response content: {response.text}")
        
        response.raise_for_status()
        
        return {
            "fastapi_message": "Successfully called n8n",
            "n8n_response": response.json(),
            "status_code": response.status_code
        }
        
    except requests.exceptions.Timeout:
        raise HTTPException(status_code=504, detail="n8n request timed out")
    except requests.exceptions.HTTPError as e:
        raise HTTPException(
            status_code=500, 
            detail=f"n8n returned error: {e.response.status_code} - {e.response.text}"
        )
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=500,
            detail=f"n8n returned non-JSON response. Status: {response.status_code}, Content: {response.text}"
        )
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Error calling n8n: {str(e)}")