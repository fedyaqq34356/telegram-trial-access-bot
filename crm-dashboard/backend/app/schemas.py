from datetime import datetime

from pydantic import BaseModel, Field

class LoginRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class RefreshRequest(BaseModel):
    refresh_token: str

class AccessItem(BaseModel):
    agency_id: int
    can_view: bool = True
    can_change_ratio: bool = False
    can_split: bool = False

class UserCreate(BaseModel):
    username: str
    password: str
    name: str = ""
    role: str = "admin"
    can_manage_users: bool = False
    can_view_traffic: bool = False
    accesses: list[AccessItem] = []

class UserUpdate(BaseModel):
    password: str | None = None
    name: str | None = None
    role: str | None = None
    can_manage_users: bool | None = None
    can_view_traffic: bool | None = None
    is_active: bool | None = None
    accesses: list[AccessItem] | None = None

class AccessOut(BaseModel):
    agency_id: int
    agency_name: str = ""
    can_view: bool
    can_change_ratio: bool
    can_split: bool

class UserOut(BaseModel):
    id: int
    username: str
    name: str
    role: str
    can_manage_users: bool
    can_view_traffic: bool = False
    is_active: bool
    created_at: datetime | None = None
    last_login: datetime | None = None
    accesses: list[AccessOut] = []

class AgencyCreate(BaseModel):
    name: str
    url: str = "https://admin.livegirl.me"
    account: str = ""
    password: str = ""
    aemail: str = ""
    apassword: str = ""
    tfa_required: bool = False

class AgencyUpdate(BaseModel):
    name: str | None = None
    url: str | None = None
    account: str | None = None
    password: str | None = None
    aemail: str | None = None
    apassword: str | None = None
    tfa_required: bool | None = None
    is_active: bool | None = None

class AgencyOut(BaseModel):
    id: int
    name: str
    url: str
    tfa_required: bool
    is_active: bool
    has_session: bool = False
    last_synced_at: datetime | None = None
    cooldown_remaining_seconds: int = 0
    can_change_ratio: bool = True
    can_split: bool = True

class RatioUpdate(BaseModel):
    ratio_percent: float = Field(ge=0, le=20)

class TfaSubmit(BaseModel):
    agency_id: int
    code: str

class SplitRequest(BaseModel):
    agency_id: int | None = None

class SettingsUpdate(BaseModel):
    values: dict[str, str]
