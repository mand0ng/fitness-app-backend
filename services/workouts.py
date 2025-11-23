from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import BackgroundTasks
from datetime import datetime
import asyncio
import json
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from config.my_logger import get_logger
from models.models import WorkoutProgram, User, WorkoutDay, WorkoutDayType
from utils.helpers import user_to_dict
from sherlock_ai.model import SherlockAI
from db.session_manager import session_manager
from concurrent.futures import ThreadPoolExecutor

class WorkoutService:
    # Class-level dictionary to share job status across instances
    jobs = {}
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.logger = get_logger(__name__, self.__class__.__name__)
        self.ai = SherlockAI()

    async def get_user_workout(self, user_id: int):
        try:
            self.logger.info(f"Getting workout for user {user_id}")
            result = await self.session.execute(
                select(WorkoutProgram)
                .options(selectinload(WorkoutProgram.days))
                .where(WorkoutProgram.user_id == user_id)
            )
            workout = result.scalars().first()
            return workout
        except Exception as e:
            self.logger.error(f"Error getting workout for user {user_id}: {e}")
            return None

    async def create_user_workout(self, user_id: int, backgroundTasks: BackgroundTasks):
        try:
            self.logger.info(f"Creating workout for user {user_id}")
            
            user = await self.session.get(User, user_id)
            
            if user is None:
                self.logger.error(f"User {user_id} not found")
                return None

            user_dict = user_to_dict(user)

            # add date today to user_dict
            user_dict["start_date"] = datetime.now().strftime("%Y-%m-%d")
            self.logger.info(f"CREATING WORKOUT FOR USER: {user_dict['name']} DATE: {user_dict['start_date']}")

            self.logger.info(f"User {user_id} found: {user_dict}")

            job_id = f"job_{user.id}_{int(datetime.utcnow().timestamp())}"
            WorkoutService.jobs[job_id] = {"status": "processing"}
            self.logger.info(f"Created job {job_id} for user {user_id}")

            backgroundTasks.add_task(self.generate_plan_task, job_id, user_dict)

            return job_id
        except Exception as e:
            self.logger.error(f"Error creating workout for user {user_id}: {e}")
            return None

    def get_job_status(self, job_id: str):
        """Get the status of a workout generation job"""
        return WorkoutService.jobs.get(job_id, {"status": "not_found"})

    async def generate_plan_task(self, job_id: str, user_dict: dict):
        try:
            self.logger.info(f"GENERATE_PLAN_TASK - START:: USER_ID: {user_dict['id']}")
            
            # FOR ACTUAL AI CALL
            # Asign another thread to do ai tasks 
            loop = asyncio.get_event_loop()
            with ThreadPoolExecutor() as pool:
                workout_plan_str = await loop.run_in_executor(pool, self.ai.generate_workout_plan, user_dict)
            
            # FOR TESTING 
            # use this when testing 
            # workout_plan_str = await self.ai.get_sample_ai_json_response()
            
            workout_plan = json.loads(workout_plan_str)

            async with session_manager.async_session() as session:
                # Create WorkoutProgram
                # Parse start_date
                start_date = datetime.strptime(workout_plan["start_date"], "%Y-%m-%d").date()
                
                program = WorkoutProgram(
                    user_id=int(user_dict['id']),
                    start_date=start_date,
                    total_days=workout_plan["total_days"],
                    notes_from_coach=workout_plan.get("notes_from_coach", "")
                )
                session.add(program)
                await session.flush() # Flush to get the program ID

                # Create WorkoutDays
                for day_data in workout_plan["plan"]:
                    day_date = datetime.strptime(day_data["date"], "%Y-%m-%d").date()
                    day_type_str = day_data["type"].lower()
                    day_type = WorkoutDayType.workout if day_type_str == "workout" else WorkoutDayType.rest
                    
                    workout_details = day_data.get("workout") if day_type == WorkoutDayType.workout else None

                    day = WorkoutDay(
                        workout_program_id=program.id,
                        day_sequence=day_data["day"],
                        date=day_date,
                        workout_day_type=day_type,
                        workout_details=workout_details
                    )
                    session.add(day)
                
                await session.commit()
                self.logger.info(f"Saved workout program {program.id} with {len(workout_plan['plan'])} days to DB")

            WorkoutService.jobs[job_id] = {"status": "completed", "workout_plan": workout_plan}

            self.logger.info(f"GENERATE_PLAN_TASK - END:: USER_ID: {user_dict['id']}")
            self.logger.info(f"WORKOUT_PLAN:: USER_ID: {user_dict['id']} :: WORKOUT-DETAILS :: {workout_plan}")
        except Exception as e:
            self.logger.error(f"Error generating workout plan for user {user_dict['id']}: {e}")
            WorkoutService.jobs[job_id] = {"status": "failed", "error": str(e)}
            
        