import json
from fastapi import FastAPI, Depends
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
import asyncio
from fastapi.middleware.cors import CORSMiddleware
import requests
from fastapi import HTTPException
import os
from dotenv import load_dotenv

def load_config():
    env = os.getenv('ENVIRONMENT', 'development')
    
    if env == 'production':
        # In production, rely on k8s ENV vars, .env is backup
        load_dotenv('.env.production', override=False)
    else:
        # In development, use .env file
        load_dotenv('.env.development', override=True)

load_config()

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

engine = create_async_engine(DATABASE_URL, echo=True)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_session():
    async with async_session() as session:
        yield session

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
        "ENV_ENVIRONMENT": os.getenv("ENV_ENVIRONMENT")
    }

@app.get("/users")
async def get_users(session: AsyncSession = Depends(get_session)):
    result = await session.execute(text("SELECT * FROM fitness.users"))
    users = result.mappings().fetchall()
    return {"users": [dict(row) for row in users]}
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