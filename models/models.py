from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, Float, Text, ForeignKey, Date
from sqlalchemy.types import ARRAY
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.dialects.postgresql import JSONB
import enum
from typing import Optional

from db.session_manager import Base

# Base = declarative_base()


class FitnessLevel(enum.Enum):
    beginner = "beginner"
    intermediate = "intermediate"
    advance = "advance"

class FitnessGoal(enum.Enum):
    lose_weight = "lose weight"
    build_muscle = "build muscle"
    improve_endurance = "improve endurance"
    general_fitness = "general fitness"

class WorkOutLocation(enum.Enum):
    home_workout = "home workout"
    gym_workout = "gym workout"
    both = "both home and gym"

class DayAvailability(enum.Enum):
    monday = "monday"
    tuesday = "tuesday"
    wednesday = "wednesday"
    thursday = "thursday"
    friday = "friday"
    saturday = "saturday"
    sunday = "sunday"

class EquipmentAvailability(enum.Enum):
    bodyweight = "bodyweight"
    dumbells = "dumbells"
    resistance_bands = "resistance bands"
    kettleballs = "kettleballs"
    pull_up_bars = "pull-up bars"
    yoga_mat = "yoga mat"
    full_gym_access = "full gym access"

class Gender(enum.Enum):
    male = "male"
    female = "female"

class WorkoutDayType(enum.Enum):
    workout = "workout"
    rest = "rest"

class User(Base):
    __tablename__ = "users"
    __table_args__ = {'schema': 'fitness'}

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    age: Mapped[int] = mapped_column(Integer, nullable=True)
    gender: Mapped[Gender] = mapped_column(ENUM(Gender), name='gender', nullable=True)
    height: Mapped[int] = mapped_column(Integer, nullable=True)
    weight: Mapped[float] = mapped_column(Float, nullable=True)
    fitness_level: Mapped[FitnessLevel] = mapped_column(ENUM(FitnessLevel), name='fitness_level', nullable=True)
    fitness_goal: Mapped[FitnessGoal] = mapped_column(ENUM(FitnessGoal), name='fitness_goal', nullable=True)
    work_out_location: Mapped[WorkOutLocation] = mapped_column(ENUM(WorkOutLocation), name='work_out_location', nullable=True)
    days_availability: Mapped[list[DayAvailability]] = mapped_column(ARRAY(ENUM(DayAvailability)), name='days_availability', nullable=True)
    equipment_availability: Mapped[list[EquipmentAvailability]] = mapped_column(ARRAY(ENUM(EquipmentAvailability)), name='equipment_availability', nullable=True)
    notes: Mapped[str] = mapped_column(Text, nullable=True)
    # orm relationship to workout programs
    workout_programs: Mapped["WorkoutProgram"] = relationship("WorkoutProgram", back_populates="user")
    
class WorkoutProgram(Base):
    __tablename__ = "workout_programs"
    __table_args__ = {'schema': 'fitness'}

    id: Mapped[int] = mapped_column(primary_key=True)
    start_date: Mapped[Date] = mapped_column(Date, nullable=False)
    total_days: Mapped[int] = mapped_column(Integer, nullable=False)
    notes_from_coach: Mapped[str] = mapped_column(Text, nullable=True)
    # db relationship to plan days
    user_id: Mapped[int] = mapped_column(ForeignKey("fitness.users.id", ondelete="CASCADE"), nullable=False)
    # orm relationship to plan days
    days: Mapped[list["WorkoutDay"]] = relationship("WorkoutDay", back_populates="workout_program")
    user: Mapped["User"] = relationship(back_populates="workout_programs")

class WorkoutDay(Base):
    __tablename__ = "workout_days"
    __table_args__ = {'schema': 'fitness'}

    id: Mapped[int] = mapped_column(primary_key=True)
    day_sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    date: Mapped[str] = mapped_column(Date, nullable=False)
    workout_day_type: Mapped[WorkoutDayType] = mapped_column(ENUM(WorkoutDayType), name='workout_day_type', nullable=False, default=WorkoutDayType.workout)
    workout_program_id: Mapped[int] = mapped_column(ForeignKey("fitness.workout_programs.id", ondelete="CASCADE"), nullable=False)
    # postgresql jsonb column to store workout details
    workout_details: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    # orm
    workout_program: Mapped["WorkoutProgram"] = relationship(back_populates="days")