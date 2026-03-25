from uuid import UUID
from pydantic import BaseModel, EmailStr
from typing import Optional, List, Any, Literal
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
    AadharNumber: str
    Address: Optional[str] = None

class UserLogin(BaseModel):
    Email: EmailStr
    Password: str
    
class UserResponse(UserBase):
    UserID: int
    RoleID: int
    CreatedAt: datetime
    UpdatedAt: datetime
    AadharNumber: str
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
        from_attributes = True


class DoctorProfileBase(BaseModel):
    DProfilePhoto: Optional[str]
    Qualification: Optional[str]
    Specialization: Optional[str]
    RegistrationNumber: Optional[str]
    ExperienceYears: Optional[int]
    ClinicAddress: Optional[str]
    AvailabilitySchedule: Optional[Any]
    PANNumber: Optional[str]
    AccountNumber: Optional[str]
    IFSCCode: Optional[str]

class DoctorProfileCreate(DoctorProfileBase):
    DoctorID: int

class DoctorProfileResponse(DoctorProfileBase):
    DoctorID: int
    class Config:
        from_attributes = True


class DoctorListResponse(BaseModel):
    DProfilePhoto: Optional[str]
    UserID: int
    FirstName: str
    LastName: Optional[str]
    Phone: str
    Specialization: Optional[str]
    ExperienceYears: Optional[int]

    class Config:
        from_attributes = True


# ✅ Renamed Employee → StaffProfile for consistency
# =========================
# ✅ Employee (Replaces StaffProfile)
# =========================

class EmployeeBase(BaseModel):
    EProfilePhoto: Optional[str]
    Division: Optional[str]
    Ward: Optional[str]
    Designation: Optional[str]
    JoinDate: Optional[date]
    Status: Optional[str]
    PANNumber: Optional[str]
    AccountNumber: Optional[str]
    IFSCCode: Optional[str]

class EmployeeCreate(EmployeeBase):
    pass  # no need for UserID, it's passed from URL

class EmployeeResponse(EmployeeBase):
    EmployeeID: int

    class Config:
        from_attributes = True


class EmployeeListResponse(BaseModel):
    EProfilePhoto: Optional[str]
    UserID: int
    FirstName: str
    LastName: Optional[str]
    Phone: str
    Division: Optional[str]
    Designation: Optional[str]
    Status: Optional[str]

    class Config:
        from_attributes = True


class PatientListResponse(BaseModel):
    UserID: int
    FirstName: str
    LastName: Optional[str]
    Phone: str
    BloodGroup: Optional[str]
    RiskCategory: Optional[str]

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

class CategorizedAppointmentsResponse(BaseModel):
    today: List[AppointmentResponse]
    past: List[AppointmentResponse]
    upcoming: List[AppointmentResponse]

class ConsultationBase(BaseModel):
    AppointmentID: int
    PrescriptionFile: Optional[str]
    FollowUpRequired: Optional[bool]

class ConsultationCreate(ConsultationBase):
    pass

class ConsultationResponse(ConsultationBase):
    ConsultationID: int
    class Config:
        from_attributes = True

class PrescriptionListResponse(BaseModel):
    ConsultationID: int
    AppointmentID: int
    DateTime: datetime
    DoctorName: Optional[str]
    PrescriptionFile: Optional[str]
    DownloadURL: Optional[str] = None
    
    class Config:
        from_attributes = True



# =========================
# 4️⃣  Labs, Investigations & Reports
# =========================

class LabCenterBase(BaseModel):
    Name: str
    Address: str
    Contact: str
    AccreditationNumber: Optional[str]
    ApprovedByAdmin: Optional[bool] = False

class LabCenterCreate(LabCenterBase):
    OwnerEmail: Optional[str] = None
    OwnerPassword: Optional[str] = None
    OwnerFirstName: Optional[str] = None
    OwnerLastName: Optional[str] = None
    OwnerPhone: Optional[str] = None
    OwnerAadharNumber: Optional[str] = None

class LabCenterResponse(LabCenterBase):
    LabID: int
    CreatedAt: datetime
    OwnerUserID: Optional[int] = None
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
    AppointmentID: Optional[int] = None
    InvestigationID: int
    InvestigationDate: Optional[date] = None
    LabID: int
    Status: Optional[str] = "PENDING"
    ResultDate: Optional[date] = None

class InvestigationBookingCreate(InvestigationBookingBase):
    pass

class InvestigationBookingResponse(InvestigationBookingBase):
    BookingID: int
    PatientName: Optional[str] = None
    InvestigationName: Optional[str] = None
    class Config:
        from_attributes = True


class BookingActionPayload(BaseModel):
    action: Literal["approve", "reject"]


class ReportBase(BaseModel):
    BookingID: int
    FilePath: str
    FileType: str

class ReportCreate(ReportBase):
    pass

class ReportResponse(ReportBase):
    ReportID: int
    FilePath: str
    FileType: str
    class Config:
        from_attributes = True


# =========================
# 5️⃣  Billing & Payments
# =========================

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

class DoctorBillingBase(BaseModel):
    AppointmentID: int
    PaymentID: Optional[int]
    Amount: float

class DoctorBillingCreate(DoctorBillingBase):
    pass



class DoctorBillingResponse(DoctorBillingBase):
    DBillID: int
    Date: datetime
    class Config:
        from_attributes = True

class LabCenterBillingBase(BaseModel):
    AppointmentID: int
    PaymentID: Optional[int] = None
    Amount: float

class LabCenterBillingCreate(LabCenterBillingBase):
    pass

class LabCenterBillingResponse(LabCenterBillingBase):
    LabBillID: int
    Date: datetime
    class Config:
        from_attributes = True







