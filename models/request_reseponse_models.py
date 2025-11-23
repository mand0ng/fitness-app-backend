from pydantic import BaseModel, EmailStr, Field
from typing import Optional

class UserDetails(BaseModel):
    id: Optional[int] = None
    email: Optional[str] = None 
    name: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    height: Optional[float] = None
    weight: Optional[float] = None
    fitness_level: Optional[str] = Field(None, alias="fitnessLevel")
    fitness_goal: Optional[str] = Field(None, alias="fitnessGoal")
    work_out_location: Optional[str] = Field(None, alias="workoutLocation")
    days_availability: Optional[list] = Field(None, alias="daysAvailability")
    equipment_availability: Optional[list] = Field(None, alias="equipmentAvailability")
    notes: Optional[str] = None
    date_now: Optional[str] = None
    password: Optional[str] = None
    
    class Config:
        populate_by_name = True
    
class UserLogin(BaseModel):
    email: EmailStr
    password: str