from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class CreateEmployeeRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=50)
    role_title: str | None = Field(default=None, max_length=200)


class UpdateEmployeeRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=50)
    role_title: str | None = Field(default=None, max_length=200)
    is_active: bool | None = None


class EmployeeResponse(BaseModel):
    id: str
    company_id: str
    name: str
    email: str | None
    phone: str | None
    role_title: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime
