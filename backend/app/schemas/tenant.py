import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from backend.app.models.enums import SensorStatus, UserRole


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class MSPCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=1, max_length=64, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class MSPRead(ORMModel):
    id: uuid.UUID
    name: str
    slug: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


class UserCreate(BaseModel):
    email: EmailStr
    full_name: str | None = Field(default=None, max_length=255)
    role: UserRole = UserRole.ANALYST


class UserRead(ORMModel):
    id: uuid.UUID
    msp_id: uuid.UUID
    email: str
    full_name: str | None
    role: UserRole
    is_active: bool
    created_at: datetime
    updated_at: datetime


class CustomerCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=1, max_length=64, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class CustomerRead(ORMModel):
    id: uuid.UUID
    msp_id: uuid.UUID
    name: str
    slug: str
    created_at: datetime
    updated_at: datetime


class SiteCreate(BaseModel):
    customer_id: uuid.UUID
    name: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=1, max_length=64, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    timezone: str = Field(default="UTC", max_length=64)


class SiteRead(ORMModel):
    id: uuid.UUID
    msp_id: uuid.UUID
    customer_id: uuid.UUID
    name: str
    slug: str
    timezone: str
    created_at: datetime
    updated_at: datetime


class SensorCreate(BaseModel):
    site_id: uuid.UUID
    name: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=1, max_length=64, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    status: SensorStatus = SensorStatus.PENDING


class SensorRead(ORMModel):
    id: uuid.UUID
    msp_id: uuid.UUID
    site_id: uuid.UUID
    name: str
    slug: str
    status: SensorStatus
    last_heartbeat_at: datetime | None
    created_at: datetime
    updated_at: datetime


class DeviceCreate(BaseModel):
    site_id: uuid.UUID
    hostname: str | None = Field(default=None, max_length=255)
    mac_address: str | None = Field(default=None, max_length=17)
    ip_address: str | None = Field(default=None, max_length=45)
    device_type: str | None = Field(default=None, max_length=64)


class DeviceRead(ORMModel):
    id: uuid.UUID
    msp_id: uuid.UUID
    site_id: uuid.UUID
    hostname: str | None
    mac_address: str | None
    ip_address: str | None
    device_type: str | None
    first_seen_at: datetime | None
    last_seen_at: datetime | None
    created_at: datetime
    updated_at: datetime
