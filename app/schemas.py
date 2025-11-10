from pydantic import BaseModel, EmailStr
from typing import Optional, List, Any
from datetime import date, datetime

# =========================
# 1️⃣  Roles & Users
# =========================

class RoleBase(BaseModel):
    RoleName: str
    Description: Optional[str]

class RoleCreate(RoleBase):
    pass

class RoleResponse(RoleBase):
    RoleID: int
    class Config:
        from_attributes = True


class UserBase(BaseModel):
    FirstName: str
    LastName: Optional[str]
    Email: EmailStr
    Phone: str

class UserCreate(UserBase):
    Password: str
    RoleID: Optional[int]
    Gender: Optional[str] = None
    DOB: Optional[date] = None
    Address: Optional[str] = None

class UserLogin(BaseModel):
    Email: EmailStr
    Password: str
    
class UserResponse(UserBase):
    UserID: int
    RoleID: int
    CreatedAt: datetime
    UpdatedAt: datetime
    Gender: Optional[str] = None
    DOB: Optional[date] = None
    Address: Optional[str] = None

    class Config:
        from_attributes = True


# =========================
# 2️⃣  Profiles
# =========================

class PatientProfileBase(BaseModel):
    Height: Optional[float]
    Weight: Optional[float]
    BloodGroup: Optional[str]
    Allergies: Optional[str]
    ChronicDiseases: Optional[str]
    RiskCategory: Optional[str]
    FamilyHistory: Optional[str]
    Lifestyle: Optional[str]

class PatientProfileCreate(PatientProfileBase):
    PatientID: int

class PatientProfileResponse(PatientProfileBase):
    PatientID: int
    class Config:
        orm_mode = True


class DoctorProfileBase(BaseModel):
    Qualification: Optional[str]
    Specialization: Optional[str]
    RegistrationNumber: Optional[str]
    ExperienceYears: Optional[int]
    ClinicAddress: Optional[str]
    AvailabilitySchedule: Optional[Any]
    AadharNumber: Optional[str]
    PANNumber: Optional[str]
    AccountNumber: Optional[str]
    IFSCCode: Optional[str]

class DoctorProfileCreate(DoctorProfileBase):
    DoctorID: int

class DoctorProfileResponse(DoctorProfileBase):
    DoctorID: int
    class Config:
        from_attributes = True


# ✅ Renamed Employee → StaffProfile for consistency
# =========================
# ✅ Employee (Replaces StaffProfile)
# =========================

class EmployeeBase(BaseModel):
    Division: Optional[str]
    Ward: Optional[str]
    Designation: Optional[str]
    JoinDate: Optional[date]
    Status: Optional[str]
    AadharNumber: Optional[str]
    PANNumber: Optional[str]
    AccountNumber: Optional[str]
    IFSCCode: Optional[str]

class EmployeeCreate(EmployeeBase):
    pass  # no need for UserID, it's passed from URL

class EmployeeResponse(EmployeeBase):
    EmployeeID: int

    class Config:
        from_attributes = True




# =========================
# 3️⃣  Appointments & Consultations
# =========================

class AppointmentBase(BaseModel):
    PatientID: int
    DoctorID: int
    DateTime: datetime
    Type: Optional[str]
    Status: Optional[str]

class AppointmentCreate(AppointmentBase):
    pass

class AppointmentResponse(AppointmentBase):
    AppointmentID: int

    class Config:
        from_attributes = True

# New schema for employee view with names
class AppointmentEmployeeResponse(BaseModel):
    AppointmentID: int
    PatientID: int
    PatientName: Optional[str]
    DoctorID: int
    DoctorName: Optional[str]
    DateTime: datetime
    Type: Optional[str]
    Status: Optional[str]

    class Config:
        from_attributes = True

class ConsultationBase(BaseModel):
    AppointmentID: int
    Notes: Optional[str]
    PrescriptionFile: Optional[str]
    FollowUpRequired: Optional[bool]

class ConsultationCreate(ConsultationBase):
    pass

class ConsultationResponse(ConsultationBase):
    ConsultationID: int
    class Config:
        from_attributes = True


# =========================
# 4️⃣  Labs, Investigations & Reports
# =========================

class LabCenterBase(BaseModel):
    Name: str
    Address: Optional[str]
    Contact: Optional[str]
    AccreditationNumber: Optional[str]
    ApprovedByAdmin: Optional[bool] = False

class LabCenterCreate(LabCenterBase):
    pass

class LabCenterResponse(LabCenterBase):
    LabID: int
    CreatedAt: datetime
    class Config:
        from_attributes = True


class InvestigationBase(BaseModel):
    Name: str
    Description: Optional[str]
    DefaultRate: Optional[float]

class InvestigationCreate(InvestigationBase):
    pass

class InvestigationResponse(InvestigationBase):
    InvestigationID: int
    class Config:
        from_attributes = True


class InvestigationBookingBase(BaseModel):
    AppointmentID: int
    InvestigationID: int
    LabID: int
    Status: Optional[str]
    ResultDate: Optional[date]

class InvestigationBookingCreate(InvestigationBookingBase):
    pass

class InvestigationBookingResponse(InvestigationBookingBase):
    BookingID: int
    class Config:
        from_attributes = True


class ReportBase(BaseModel):
    BookingID: int
    FilePath: str
    AbnormalFlag: Optional[bool]

class ReportCreate(ReportBase):
    pass

class ReportResponse(ReportBase):
    ReportID: int
    class Config:
        from_attributes = True


# =========================
# 5️⃣  Billing & Payments
# =========================

class DiscountBase(BaseModel):
    Name: str
    Rule: Optional[Any]
    StartDate: Optional[date]
    EndDate: Optional[date]
    Percent: Optional[float]

class DiscountCreate(DiscountBase):
    pass

class DiscountResponse(DiscountBase):
    DiscountID: int
    class Config:
        from_attributes = True


class PaymentBase(BaseModel):
    Method: str
    TransactionRef: Optional[str]
    Status: Optional[str]

class PaymentCreate(PaymentBase):
    pass

class PaymentResponse(PaymentBase):
    PaymentID: int
    Date: datetime
    class Config:
        from_attributes = True


class BillingBase(BaseModel):
    AppointmentID: int
    PaymentID: int
    DiscountID: Optional[int]
    Amount: float
    FinalAmount: float

class BillingCreate(BillingBase):
    pass

class BillingResponse(BillingBase):
    BillID: int
    Date: datetime
    class Config:
        from_attributes = True


# =========================
# 6️⃣  Attendance
# =========================

class AttendanceBase(BaseModel):
    UserID: int
    Date: date
    InTime: Optional[datetime]
    OutTime: Optional[datetime]
    Latitude: Optional[float]
    Longitude: Optional[float]
    Remarks: Optional[str]

class AttendanceCreate(AttendanceBase):
    pass

class AttendanceResponse(AttendanceBase):
    AttendanceID: int
    class Config:
        from_attributes = True
