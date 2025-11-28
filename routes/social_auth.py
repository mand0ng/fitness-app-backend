from fastapi import APIRouter, Depends, HTTPException, Header, status
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.responses import JSONResponse
import firebase_admin
from firebase_admin import auth, credentials
import os
import secrets
import string

from models.models import User
from services.users import UserService
from db.session_manager import get_session
from utils.helpers import create_access_token, user_to_dict
from config.my_logger import get_logger

# Initialize Firebase Admin
# Check if app is already initialized to avoid errors on reload
if not firebase_admin._apps:
    # Try to load from service account file if it exists
    cred_path = os.getenv("FIREBASE_CREDENTIALS_PATH", "serviceAccountKey.json")
    if os.path.exists(cred_path):
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
    else:
        # Fallback for development without service account (might limit some features)
        # or rely on default credentials if on GCP
        print(f"Warning: {cred_path} not found. Firebase Admin might not work correctly for token verification.")
        try:
            firebase_admin.initialize_app()
        except Exception as e:
            print(f"Failed to initialize Firebase Admin: {e}")

socialAuthRoutes = APIRouter(
    prefix="/auth",
    tags=["Social Authentication"]
)

logger = get_logger(__name__, "social_auth")

class SocialLoginRequest:
    def __init__(self, token: str):
        self.token = token

def generate_random_password(length=12):
    alphabet = string.ascii_letters + string.digits + string.punctuation
    return ''.join(secrets.choice(alphabet) for i in range(length))

@socialAuthRoutes.post("/social-login/")
async def social_login(request: dict, session: AsyncSession = Depends(get_session)):
    token = request.get("token")
    if not token:
        return JSONResponse(status_code=400, content={"status": "error", "message": "Token is required"})

    try:
        # Verify Firebase Token
        decoded_token = auth.verify_id_token(token)
        email = decoded_token.get("email")
        name = decoded_token.get("name", "")
        uid = decoded_token.get("uid")

        if not email:
            return JSONResponse(status_code=400, content={"status": "error", "message": "Email not found in token"})

        user_service = UserService(session)
        user = await user_service.get_user_by_email(email)

        if not user:
            # Create new user
            # Generate a dummy password since they use social login
            dummy_password = generate_random_password()
            # Hash it if your User model expects hashed password (it usually does)
            # Assuming you have a hashing utility, but for now we'll just store it 
            # (In a real app, use the same hashing as your normal auth)
            from passlib.context import CryptContext
            pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
            hashed_password = pwd_context.hash(dummy_password)

            new_user = User(
                email=email,
                name=name,
                password=hashed_password,
                # Set default values or leave null
            )
            user = await user_service.create_user(new_user)
            if not user:
                 return JSONResponse(status_code=500, content={"status": "error", "message": "Failed to create user"})

        # Generate JWT for your backend
        access_token = create_access_token(data={"sub": user.email})

        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "access_token": access_token,
                "user": user_to_dict(user)
            }
        )

    except Exception as e:
        logger.error(f"Social login error: {e}")
        return JSONResponse(status_code=401, content={"status": "error", "message": f"Invalid token or auth error: {str(e)}"})


@socialAuthRoutes.delete("/users/me")
async def delete_account(authorization: str = Header(...), session: AsyncSession = Depends(get_session)):
    try:
        if not authorization or not authorization.startswith("Bearer "):
            return JSONResponse(status_code=401, content={"status": "error", "message": "Unauthorized"})

        token = authorization.split(" ")[1]
        # Verify your backend JWT
        import jwt
        SECRET_KEY = os.getenv("SECRET_KEY")
        ALGORITHM = os.getenv("ALGORITHM")
        
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            email = payload.get("sub")
        except jwt.PyJWTError:
             return JSONResponse(status_code=401, content={"status": "error", "message": "Invalid token"})

        user_service = UserService(session)
        user = await user_service.get_user_by_email(email)

        if not user:
            return JSONResponse(status_code=404, content={"status": "error", "message": "User not found"})

        # Delete user
        # Assuming UserService has a delete method or we do it manually
        # If UserService doesn't have delete, we can add it or do it here
        await session.delete(user)
        await session.commit()

        return JSONResponse(status_code=200, content={"status": "success", "message": "Account deleted successfully"})

    except Exception as e:
        logger.error(f"Delete account error: {e}")
        return JSONResponse(status_code=500, content={"status": "error", "message": "Internal server error"})

@socialAuthRoutes.post("/users/delete-callback")
async def delete_callback(request: dict):
    # This is for Facebook's data deletion callback
    # You just need to log it and return a confirmation code
    logger.info(f"Delete callback received: {request}")
    return JSONResponse(status_code=200, content={"url": "https://getfit.com/data-deletion-status", "confirmation_code": "12345"})
