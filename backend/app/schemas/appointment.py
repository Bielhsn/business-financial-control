from datetime import datetime

from pydantic import BaseModel, Field

from app.domain.appointment.entities import AppointmentStatus


class CreateAppointmentRequest(BaseModel):
    title: str | None = Field(default=None, max_length=200)
    starts_at: datetime
    duration_minutes: int = Field(gt=0, le=24 * 60)
    client_id: str | None = None
    employee_id: str | None = None
    catalog_item_id: str | None = None
    price_cents: int | None = Field(default=None, ge=0)
    notes: str | None = Field(default=None, max_length=2000)


class UpdateAppointmentRequest(BaseModel):
    title: str | None = Field(default=None, max_length=200)
    starts_at: datetime | None = None
    duration_minutes: int | None = Field(default=None, gt=0, le=24 * 60)
    price_cents: int | None = Field(default=None, ge=0)
    notes: str | None = Field(default=None, max_length=2000)


class ChangeAppointmentStatusRequest(BaseModel):
    status: AppointmentStatus


class AppointmentResponse(BaseModel):
    id: str
    company_id: str
    title: str
    starts_at: datetime
    duration_minutes: int
    status: AppointmentStatus
    client_id: str | None
    client_name: str | None
    employee_id: str | None
    employee_name: str | None
    catalog_item_id: str | None
    price_cents: int | None
    notes: str | None
    revenue_transaction_id: str | None
    created_at: datetime
    updated_at: datetime
