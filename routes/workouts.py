
"""
Routes for workout management.
"""
from fastapi import APIRouter, Header, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from config.env_vars import load_config
from config.my_logger import get_logger
from db.session_manager import get_session
from services.users import UserService
from services.workouts import WorkoutService
from utils.helpers import get_email_from_token, is_user_done_onboarding, workout_program_to_dict

load_config()

workoutRoutes = APIRouter(
    prefix="/workout",
    tags=["Workouts"]
)

logger = get_logger(__name__, "workouts")


@workoutRoutes.post("/get-user-workout/{user_id}/")
async def get_user_workout(
    authorization: str = Header(...),
    session: AsyncSession = Depends(get_session)
):
    """
    Get the workout details for a specific user.
    """

    token = authorization.split(" ")[1]
    email = get_email_from_token(token)

    # first get user
    user_service = UserService(session)
    user = await user_service.get_user_by_email(email)
    if user is None:
        return JSONResponse(
            status_code=200,
            content={"status":"error", "message":"No user found."}
        )

    if not is_user_done_onboarding(user):
        return JSONResponse(
            status_code=200,
            content={"status": "error", "message": "User not complete details. "}
        )

    # check if user has workout data
    workout_service = WorkoutService(session)
    workout = await workout_service.get_user_workout(user.id)
    if workout is None:
        return JSONResponse(status_code=200, content={"status":"error", "message":"No workout found."})


    # return workout
    return JSONResponse(status_code=200, content={"status":"success", "workout": workout_program_to_dict(workout)})

@workoutRoutes.post("/create-user-workout/{user_id}/")
async def create_user_workout(
    authorization: str = Header(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    session: AsyncSession = Depends(get_session)
):
    """
    Create a new workout for a specific user.
    """
    token = authorization.split(" ")[1]
    email = get_email_from_token(token)
    user_service = UserService(session)
    user = await user_service.get_user_by_email(email)
    if user is None:
        return JSONResponse(
            status_code=200,
            content={"status":"error", "message":"No user found."}
        )
    
    if not is_user_done_onboarding(user):
        return JSONResponse(
            status_code=200,
            content={"status": "error", "message": "User not complete details. "}
        )
    
    workout_service = WorkoutService(session)

    # check first if user has workout data
    # when testing comment this out
    workout = await workout_service.get_user_workout(user.id)
    if workout is not None:
        return JSONResponse(status_code=200, content={"status":"error", "message":"User already has a workout."})

    # create workout job
    workout_job_id = await workout_service.create_user_workout(user.id, background_tasks)
    
    if workout_job_id is None:
        return JSONResponse(status_code=200, content={"status":"error", "message":"Failed to create workout job."})
    
    # return job_id for polling
    return JSONResponse(status_code=200, content={"status":"success", "job_id": workout_job_id})

@workoutRoutes.get("/job-status/{job_id}/")
async def get_job_status(
    job_id: str,
    authorization: str = Header(...),
    session: AsyncSession = Depends(get_session)
):
    """
    Get the status of a workout generation job.
    """
    token = authorization.split(" ")[1]
    email = get_email_from_token(token)
    user_service = UserService(session)
    user = await user_service.get_user_by_email(email)
    if user is None:
        return JSONResponse(
            status_code=200,
            content={"status":"error", "message":"No user found."}
        )
    
    workout_service = WorkoutService(session)
    job_status = workout_service.get_job_status(job_id)
    
    return JSONResponse(status_code=200, content={"status":"success", "job_status": job_status})