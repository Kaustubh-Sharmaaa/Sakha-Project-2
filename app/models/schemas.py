from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class Role(str, Enum):
    admin = "admin"
    user = "user"


# ---- Auth ----
class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)
    name: str
    org_id: Optional[str] = None  # Provided for admin users only


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


# ---- User ----
class UserOut(BaseModel):
    id: str
    email: EmailStr
    name: str
    org_id: str
    role: Role
    created_at: Optional[datetime] = None


# ---- Project ----
class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class ProjectOut(BaseModel):
    id: str
    name: str
    description: Optional[str]
    org_id: str
    created_by: str
    created_at: Optional[datetime] = None


# ---- Task ----
class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    project_id: str
    status: Optional[str] = "todo"
    priority: Optional[str] = "medium"


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None


class TaskOut(BaseModel):
    id: str
    title: str
    description: Optional[str]
    project_id: str
    org_id: str
    status: str
    priority: str
    assigned_to: Optional[str] = None
    created_by: str
    created_at: Optional[datetime] = None
