from fastapi import APIRouter, Depends, HTTPException, Header, status
from sqlalchemy.ext.asyncio import AsyncSession
from passlib.context import CryptContext
from fastapi.responses import JSONResponse
import jwt, os

from models.models import User
from models.request_reseponse_models import UserLogin
from services.users import UserService
from db.session_manager import get_session
from utils.helpers import create_access_token, user_to_dict
from config.env_vars import load_config
from config.my_logger import get_logger


load_config()

authRoutes = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
logger = get_logger(__name__, "authentticate")


SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")

# TODO: 
# - ADD TRUE LOGOUT, TOKEN BLACKLISTING   
@authRoutes.post("/login/")
async def login_user(credentials: UserLogin, session: AsyncSession = Depends(get_session)):
    try:
        user_service = UserService(session)     
        user = await user_service.get_user_by_email(credentials.email)
        
        if not user or not pwd_context.verify(credentials.password, user.password):
            return JSONResponse(status_code=401, content={"status": "error", "message": "Invalid email or password"})
        access_token = create_access_token(data={"sub": user.email})
        return JSONResponse(
            status_code=200,
            content={
                "status": "success", 
                "access_token": access_token,
                "user" : user_to_dict(user)
            }
        )
    except Exception as e:
        logger.error(f"Login error: {e}")
        return JSONResponse(status_code=500, content={"status": "error", "message": "Internal server error"})

@authRoutes.post("/check-token/")
async def check_token(authorization : str = Header(...), session: AsyncSession = Depends(get_session)):
    try:
        if not authorization or not authorization.startswith("Bearer "):
            return JSONResponse(status_code=200, content={"status": "error", "message": "No authorization header provided"})

        token = authorization.split(" ")[1]
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        
        user_service = UserService(session)
        user = await user_service.get_user_by_email(email)
        if user is None:
            return JSONResponse(status_code=200, content={"status": "error", "message": "No user found for this token"})
        
        if (
           user.age is None or 
           user.weight is None or 
           user.height is None or 
           user.gender is None or
           user.fitness_level is None or 
           user.fitness_goal is None or 
           user.work_out_location is None or 
           user.days_availability is None or 
           user.equipment_availability is None or
           user.notes is None
        ):
            onboarding_status = "incomplete"
        else:
            onboarding_status = "complete"    
            
        return JSONResponse(
            status_code=200,
            content={
                "status": "success", 
                "onboarding_status": onboarding_status,
                "access_token": token,
                "user": user_to_dict(user)
            }
                
        )
    except Exception as e:
        logger.error(f"Token validation error: {e}")
        if isinstance(e, jwt.PyJWTError):
            return JSONResponse(status_code=200, content={"status": "error", "message": "Invalid Token"})
            
        return JSONResponse(status_code=401, content={"status": "error", "message": "Invalid token"})