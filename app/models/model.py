from typing import Optional, List
from pydantic import BaseModel, EmailStr


class User(BaseModel):
    username: str
    email: EmailStr
    full_name: Optional[str]
    hashed_password: str
    company_id: Optional[str] = None
    designation: str
    salary: float


class UpdateUser(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    hashed_password: Optional[str] = None
    company_id: Optional[str] = None  
    designation: Optional[str] = None
    salary: Optional[float] = None


class Company(BaseModel):
    company_name: str
    location: str
    est_year: Optional[float] = None
    # users: Optional[List[User]] = None  


class UpdateCompany(BaseModel):
    company_name: Optional[str] = None
    location: Optional[str] = None
    est_year: Optional[float] = None
    # users: Optional[List[str]] = None
    
  

class Token(BaseModel):
    access_token: str
    token_type: str


    




        
