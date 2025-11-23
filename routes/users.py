from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Header, BackgroundTasks
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from passlib.context import CryptContext
from fastapi.responses import JSONResponse
from sqlalchemy import select, and_
import jwt, os

from config.my_logger import get_logger
from db.session_manager import get_session
from models.models import User
from sherlock_ai.model import SherlockAI
from models.request_reseponse_models import UserDetails, UserLogin
from services.users import UserService
from utils.helpers import get_email_from_token, hash_password, create_access_token, user_to_dict, user_to_model

logger = get_logger(__name__, "users")

userRoutes = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
ai = SherlockAI()

@userRoutes.post("/create-user/")
async def create_user(user: UserDetails, session: AsyncSession = Depends(get_session)):
    
    user_service = UserService(session)
    existing_user = await user_service.get_user_by_email(user.email)
    if existing_user:
        return JSONResponse(
            status_code=400, 
            content={
                "status":"error", 
                "message":"Email already exists."
            }
        )    
    
    hashed_password = hash_password(user.password)
    new_user = User(
        email=user.email,
        password=hashed_password,
        name=user.name,
        age=user.age,
        weight=user.weight,
        fitness_level=user.fitness_level,
        fitness_goal=user.fitness_goal,
        work_out_location=user.work_out_location,
        days_availability=user.days_availability,
        equipment_availability=user.equipment_availability,
        notes=user.notes
    )
    
    newly_created_user = await user_service.create_user(new_user)
    if not newly_created_user:
        return JSONResponse(
            status_code=400, 
            content={
                "status":"error", 
                "message":"Something went wrong while creating the user."
            }
        )
    
    token = create_access_token(data={"sub": newly_created_user.email})
    
    # TODO : delete user details outside user obj
    return JSONResponse(
        status_code=201, 
        content={
            "status":"success", 
            "message": "User created successfully", 
            "user_id": newly_created_user.id,
            "token" : token,
            "user": {
                "id": newly_created_user.id,
                "email": newly_created_user.email,
                "name": newly_created_user.name
        }})
    
    
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
    
jobs = {}
def generate_plan_task(job_id : str, user_details: UserDetails, ai : SherlockAI) -> None:
    logger.info(f"GENERATE-PLAN-TASK:: START - Generating plan for job {job_id}")
    try:
        workout_program_text = ai.generate_workout_plan_test(user_details)
        
        # TODO: ADD A CLEANER FOR JOBS
        jobs[job_id] = {"status": "completed", "workout_program": workout_program_text}
        
        # TODO : store workout plan
        save_workout_program(user_details, workout_program_text)
        
        
    except Exception as e:
        jobs[job_id] = {"status": "error", "message": str(e)}
        logger.error(f"GENERATE-PLAN-TASK::Error generating plan for job {job_id}: {e}")
        
def save_workout_program(user_details: UserDetails, workout_program_text: str):
        pass
    
def update_user_details(user: User, user_details: UserDetails):
    if user_details.age is not None:
        user.age = user_details.age
    if user_details.weight is not None:
        user.weight = user_details.weight
    if user_details.height is not None:
        user.height = user_details.height
    if user_details.fitness_level is not None:
        user.fitness_level = user_details.fitness_level
    if user_details.fitness_goal is not None:
        user.fitness_goal = user_details.fitness_goal
    if user_details.work_out_location is not None:
        user.work_out_location = user_details.work_out_location
    if user_details.days_availability is not None:
        user.days_availability = user_details.days_availability
    if user_details.equipment_availability is not None:
        user.equipment_availability = user_details.equipment_availability
    if user_details.notes is not None:
        user.notes = user_details.notes
    # if user_details.email not in (None, ""):
        # user.email = user_details.email
    return user
    
@userRoutes.post("/generate-30-day-plan/")
async def generate_30_day_plan(
    request_user_details: UserDetails, 
    authorization: str = Header(...), 
    session: AsyncSession = Depends(get_session),
    backgroundTasks: BackgroundTasks = BackgroundTasks()
):
    try:
        token = authorization.split(" ")[1]
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        
        # update user details
        if request_user_details.id is None and email is None:
            return JSONResponse(status_code=400, content={"status": "error", "message": "User ID or email must be provided"})
        
        result = await session.execute(
            select(User).where(
                and_(
                    User.email == email,
                    User.id == request_user_details.id
                )
            )
        )
        
        user = result.scalar_one_or_none()
        if not user:
            return JSONResponse(status_code=404, content={"status": "error", "message": "User not found"})

        user = update_user_details(user, request_user_details)
        
        try:
            await session.commit()
            await session.refresh(user)
        except IntegrityError as e:
            logger.error(f"GENERATE-30-DAY-PLAN::IntegrityError while updating user: {e}")
            await session.rollback()
            raise HTTPException(status_code=400, detail="Something went wrong while updating the user.")
        
        
        # # re-fetch user to ensure all details are current
        # result = await session.execute(
        #     select(User).where(
        #         and_(
        #             User.email == email,
        #             User.id == request_user_details.id
        #         )
        #     )
        # )
        
        # user = result.scalar_one_or_none()
        # if not user:
        #     return JSONResponse(status_code=404, content={"status": "error", "message": "User not found"})
        
        #check all required fields are filled
        if user.age is None or user.weight is None or user.height is None or user.fitness_level is None or user.fitness_goal is None or user.work_out_location is None or user.days_availability is None or user.equipment_availability is None:
            logger.info(f"GENERATE-30-DAY-PLAN::User {user.email} has incomplete details.")
            return JSONResponse(status_code=400, content={"status": "error", "message": "All user details must be completed before generating a plan"})
        
        # create 30 day plan
        job_id = f"job_{user.id}_{int(datetime.utcnow().timestamp())}"
        jobs[job_id] = {"status": "processing"}
        
        user_details_for_ai = UserDetails(
            id=user.id,
            email=user.email,
            name=user.name,
            age=user.age,
            height=user.height,
            weight=user.weight,
            fitness_level=user.fitness_level,
            fitness_goal=user.fitness_goal,
            work_out_location=user.work_out_location,
            days_availability=user.days_availability,
            equipment_availability=user.equipment_availability,
            notes=user.notes,
            date_now=request_user_details.date_now  # Pass the date from the request
        )
        
        backgroundTasks.add_task(generate_plan_task, job_id, user_details_for_ai, ai)
        
        return JSONResponse(
            status_code=200, 
            content={
                "status": "success", 
                "plan_id": job_id
            }
        )
    except Exception as e:
        logger.error(f"GENERATE-30-DAY-PLAN::Error: {e}")
        return JSONResponse(status_code=401, content={"status": "error", "message": "Invalid or expired token"})

@userRoutes.get("/plan-status/{job_id}/")
async def get_plan_status(job_id: str):
    logger.info(f"PLAN-STATUS:: list of jobs: {jobs}")
    job = jobs.get(job_id)
    if not job:
        return JSONResponse(status_code=404, content={"status": "error", "message": "Job not found"})
    return JSONResponse(status_code=200, content={"status": "success", "job": job})

@userRoutes.get("/plan-result/{job_id}/")
async def plan_result(job_id: str):
    job = jobs.get(job_id)
    if not job:
        return JSONResponse(status_code=404, content={"status": "error", "message": "Job not found"})
    if job["status"] == "completed":
        return JSONResponse(status_code=200, content={"status": "success", "plan": job["plan"]})
    elif job["status"] == "error":
        return JSONResponse(status_code=500, content={"status": "error", "message": job["message"]})
    else:
        return JSONResponse(status_code=202, content={"status": "processing"})
    
@userRoutes.get("/chat/")
async def chat_with_openai():
    response = ai.test_openai_connection()
    return JSONResponse(
        status_code=200,
        content={
            "status": "success",
            "response": response
        }
    )

@userRoutes.put("/update-user-details/{user_id}/")
async def update_user(
    user_id: int, 
    user_update_request: UserDetails, 
    authorization: str = Header(...), 
    session: AsyncSession = Depends(get_session)
    ):

    user_service = UserService(session)
    
    token = authorization.split(" ")[1]
    email = get_email_from_token(token)
    user = await user_service.get_user_by_id(user_id)

    if email is None or user is None or user.email != email:
        return JSONResponse(status_code=401, content={"status": "error", "message": "Invalid User or expired token"})

    user_update = user_to_model(user_update_request)
    # use the request model to get the keys that were sent
    update_data_keys = user_update_request.model_dump(exclude_unset=True).keys()
    
    logger.info(f"Mandong-UPDATE-USER::Keys to update: {update_data_keys}")
    try:
        for key in update_data_keys:
            # get the value from the converted model (user_update) instead of the request dict
            # because user_update has the correct Enum objects
            value = getattr(user_update, key)
            logger.info(f"Mandong-UPDATE-USER::Updating {key} to {value} from {getattr(user, key)}")
            setattr(user, key, value)
        
        updated_user = await user_service.update_user(user)
        logger.info(f"UPDATE-USER::Updated user {user_id}: {updated_user}")
    except Exception as e:
        logger.error(f"UPDATE-USER::Error updating user {user_id}: {e}")
        return JSONResponse(
            status_code=500, 
            content={
                "status":"error", 
                "message":f"Failed to update user {user.name}"
            }
        )
    
    return JSONResponse(
        status_code=200, 
        content={
            "status": "success",
            "message": "User updated successfully",
            "user": user_to_dict(updated_user)
        })
    
@userRoutes.post("/test-chain-prompt/")
async def test_chain_prompt(backgroundTasks: BackgroundTasks = BackgroundTasks()):
    try:
        job_id = f"job_{32}_{int(datetime.utcnow().timestamp())}"
        jobs[job_id] = {"status": "processing"}
        
        user_details_for_ai = UserDetails(
            id=32,
            email="name4@test.com",
            name="name4",
            age=29,
            height=157.48,
            weight=60,
            fitness_level="intermediate",
            fitness_goal="general_fitness",
            work_out_location="gym_workout",
            days_availability=[
                "tuesday",
                "wednesday",
                "thursday",
                "friday",
                "saturday"
            ],
            equipment_availability=[
                "full_gym_access",
                "yoga_mat"
            ],
            notes="physically fit",
            date_now="2025-11-18"
        )
        
        backgroundTasks.add_task(generate_plan_task, job_id, user_details_for_ai, ai)
        
        return JSONResponse(
            status_code=200, 
            content={
                "status": "success", 
                "plan_id": job_id
            }
        )
    except Exception as e:
        logger.error(f"TEST-CHAIN-PROMPT::Error occurred: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": "An error occurred while processing the request."
            }
        )
