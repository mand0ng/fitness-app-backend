from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
import jwt, os

from config.env_vars import load_config
from config.my_logger import get_logger
from models.models import User, Gender, FitnessLevel, FitnessGoal, WorkOutLocation, DayAvailability, EquipmentAvailability

load_config()
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")

logger = get_logger(__name__, "helpers")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=60)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_email_from_token(token: str) -> str | None:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        return email
    except Exception as e:
        logger.error(f"Error decoding JWT token: {e}")
        return None

def hash_password(password: str, pwd_context: CryptContext = pwd_context) -> str:
    return pwd_context.hash(password)

def user_to_dict(user) -> dict:
    """
    Converts a User SQLAlchemy model instance to a dictionary, 
    handling Enum values and Lists of Enums.
    """
    if not user:
        return {}
        
    return {
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "gender": user.gender.value if user.gender else None,
        "age": user.age,
        "weight": user.weight,
        "height": user.height,
        "fitnessLevel": user.fitness_level.value if user.fitness_level else None,
        "fitnessGoal": user.fitness_goal.value if user.fitness_goal else None,
        "workoutLocation": user.work_out_location.value if user.work_out_location else None,
        "daysAvailability": [d.value for d in user.days_availability] if user.days_availability else [],
        "equipmentAvailability": [e.value for e in user.equipment_availability] if user.equipment_availability else [],
        "notes": user.notes
    }

def user_to_model(user) -> User:
    """
    Converts a dictionary to a User SQLAlchemy model instance, 
    handling Enum values and Lists of Enums.
    """
    if not user:
        return None
        
    return User(
        id=user.id,
        email=user.email,
        name=user.name,
        gender=Gender(user.gender) if user.gender else None,
        age=user.age,
        weight=user.weight,
        height=user.height,
        fitness_level=FitnessLevel(user.fitness_level) if user.fitness_level else None,
        fitness_goal=FitnessGoal(user.fitness_goal) if user.fitness_goal else None,
        work_out_location=WorkOutLocation(user.work_out_location) if user.work_out_location else None,
        days_availability=[DayAvailability(d) for d in user.days_availability] if user.days_availability else [],
        equipment_availability=[EquipmentAvailability(e) for e in user.equipment_availability] if user.equipment_availability else [],
        notes=user.notes
    )

def is_user_done_onboarding(user) -> bool:
    if user is None:
        return False
    
    if (
        user.age is None or
        user.weight is None or
        user.height is None or
        user.gender is None or
        user.fitness_level is None or
        user.fitness_goal is None or
        user.work_out_location is None or
        user.days_availability is None or
        user.equipment_availability is None
        # user.equipment_availability is None or
        # user.notes is None
    ):
        return False
    else:
        return True

def workout_program_to_dict(workout_program) -> dict:
    """
    Converts a WorkoutProgram SQLAlchemy model instance to a dictionary,
    including its related WorkoutDay objects.
    """
    if not workout_program:
        return {}

    # Sort days by sequence to ensure order
    sorted_days = sorted(workout_program.days, key=lambda x: x.day_sequence) if workout_program.days else []

    plan = []
    for day in sorted_days:
        day_dict = {
            "day": day.day_sequence,
            "date": day.date.strftime("%Y-%m-%d") if day.date else None,
            "type": day.workout_day_type.value if day.workout_day_type else None
        }
        if day.workout_details:
            day_dict["workout"] = day.workout_details
        
        plan.append(day_dict)

    return {
        "id": workout_program.id,
        "user_id": workout_program.user_id,
        "start_date": workout_program.start_date.strftime("%Y-%m-%d") if workout_program.start_date else None,
        "total_days": workout_program.total_days,
        "notes_from_coach": workout_program.notes_from_coach,
        "plan": plan
    }