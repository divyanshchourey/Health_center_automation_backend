from sqlalchemy import (  # pyright: ignore[reportMissingImports]
    Column, Integer, String, Text, Date, DateTime, Boolean, Float, DECIMAL,
    ForeignKey, JSON
)
from sqlalchemy.orm import relationship  # pyright: ignore[reportMissingImports]
from datetime import datetime
from app.database import Base

# =========================
# 1️⃣  Roles & Users
# =========================

class Role(Base):
    __tablename__ = "Roles"

    RoleID = Column(Integer, primary_key=True, index=True)
    RoleName = Column(String, nullable=False, unique=True)
    Description = Column(Text)

    users = relationship("User", back_populates="role")


class User(Base):
    __tablename__ = "Users"

    UserID = Column(Integer, primary_key=True, index=True)
    FirstName = Column(String, nullable=False)
    LastName = Column(String)
    Email = Column(String, unique=True, nullable=False)
    Phone = Column(String, unique=True, nullable=False)
    Password = Column(String, nullable=False)
    Gender = Column(String)
    DOB = Column(Date)
    Address = Column(Text)
    AadharNumber = Column(String, nullable=False, unique=True)
    RoleID = Column(Integer, ForeignKey("Roles.RoleID"), nullable=False)
    CreatedAt = Column(DateTime, default=datetime.utcnow)
    UpdatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    role = relationship("Role", back_populates="users")
    employee = relationship("Employee", back_populates="user", uselist=False, cascade="all, delete")
    doctor = relationship("DoctorProfile", back_populates="user", uselist=False, cascade="all, delete")
    patient = relationship("PatientProfile", back_populates="user", uselist=False, cascade="all, delete")


# =========================
# 2️⃣  Profiles
# =========================

class PatientProfile(Base):
    __tablename__ = "PatientProfiles"

    PatientID = Column(Integer, ForeignKey("Users.UserID"), primary_key=True)
    Height = Column(Float)
    Weight = Column(Float)
    BloodGroup = Column(String)
    Allergies = Column(Text)
    ChronicDiseases = Column(Text)
    RiskCategory = Column(String)
    FamilyHistory = Column(Text)
    Lifestyle = Column(Text)

    user = relationship("User", back_populates="patient")
    appointments = relationship("Appointment", back_populates="patient")


class DoctorProfile(Base):
    __tablename__ = "DoctorProfiles"

    DoctorID = Column(Integer, ForeignKey("Users.UserID"), primary_key=True)
    Qualification = Column(String)
    Specialization = Column(String)
    RegistrationNumber = Column(String)
    DProfilePhoto = Column(String)
    ExperienceYears = Column(Integer)
    ClinicAddress = Column(Text)
    AvailabilitySchedule = Column(JSON)
    PANNumber = Column(String(10), unique=True)
    AccountNumber = Column(String)
    IFSCCode = Column(String)

    user = relationship("User", back_populates="doctor")
    appointments = relationship("Appointment", back_populates="doctor")

    @property
    def ImageID(self):
        return self.DoctorID

    @property
    def UserID(self):
        return self.DoctorID

    @property
    def RoleType(self):
        return "doctor"

    @property
    def StorageBucket(self):
        return "profile_image"

    @StorageBucket.setter
    def StorageBucket(self, value):
        # Kept for API compatibility; storage bucket is fixed.
        return None

    @property
    def FilePath(self):
        return self.DProfilePhoto

    @FilePath.setter
    def FilePath(self, value):
        self.DProfilePhoto = value

    @property
    def FileName(self):
        if not self.DProfilePhoto:
            return None
        return self.DProfilePhoto.rsplit("/", 1)[-1]

    @FileName.setter
    def FileName(self, value):
        return None

    @property
    def ContentType(self):
        return "image/jpeg"

    @ContentType.setter
    def ContentType(self, value):
        return None

    @property
    def UploadedAt(self):
        return datetime.utcnow()

    @UploadedAt.setter
    def UploadedAt(self, value):
        return None

    @property
    def UpdatedAt(self):
        return datetime.utcnow()

    @UpdatedAt.setter
    def UpdatedAt(self, value):
        return None


class Employee(Base):
    __tablename__ = "Employees"

    EmployeeID = Column(Integer,ForeignKey("Users.UserID"), primary_key=True)
    Division = Column(String)
    Ward = Column(String)
    Designation = Column(String)
    EProfilePhoto = Column(String)
    JoinDate = Column(Date)
    Status = Column(String)
    PANNumber = Column(String(10), unique=True)
    AccountNumber = Column(String)
    IFSCCode = Column(String)

    user = relationship("User", back_populates="employee")

    @property
    def ImageID(self):
        return self.EmployeeID

    @property
    def UserID(self):
        return self.EmployeeID

    @property
    def RoleType(self):
        return "employee"

    @property
    def StorageBucket(self):
        return "profile_image"

    @StorageBucket.setter
    def StorageBucket(self, value):
        # Kept for API compatibility; storage bucket is fixed.
        return None

    @property
    def FilePath(self):
        return self.EProfilePhoto

    @FilePath.setter
    def FilePath(self, value):
        self.EProfilePhoto = value

    @property
    def FileName(self):
        if not self.EProfilePhoto:
            return None
        return self.EProfilePhoto.rsplit("/", 1)[-1]

    @FileName.setter
    def FileName(self, value):
        return None

    @property
    def ContentType(self):
        return "image/jpeg"

    @ContentType.setter
    def ContentType(self, value):
        return None

    @property
    def UploadedAt(self):
        return datetime.utcnow()

    @UploadedAt.setter
    def UploadedAt(self, value):
        return None

    @property
    def UpdatedAt(self):
        return datetime.utcnow()

    @UpdatedAt.setter
    def UpdatedAt(self, value):
        return None

# =========================
# 3️⃣  Appointments & Consultations
# =========================

class Appointment(Base):
    __tablename__ = "Appointments"

    AppointmentID = Column(Integer, primary_key=True, index=True)
    PatientID = Column(Integer, ForeignKey("PatientProfiles.PatientID"))
    DoctorID = Column(Integer, ForeignKey("DoctorProfiles.DoctorID"))
    LabID = Column(Integer, ForeignKey("LabCenters.LabID"), nullable=True)
    DateTime = Column(DateTime)
    Type = Column(String)
    Status = Column(String)
    PaymentID = Column(Integer, ForeignKey("Payments.PaymentID"), nullable=True)

    patient = relationship("PatientProfile",back_populates="appointments")
    doctor = relationship("DoctorProfile", back_populates="appointments")
    lab = relationship("LabCenter", back_populates="appointments")
   

class Consultation(Base):
    __tablename__ = "Consultations"

    ConsultationID = Column(Integer, primary_key=True, index=True)
    AppointmentID = Column(Integer, ForeignKey("Appointments.AppointmentID"))
    PrescriptionFile = Column(Text)
    FollowUpRequired = Column(Boolean)

    appointment = relationship("Appointment")

# =========================
# 4️⃣  Labs, Investigations & Reports
# =========================

class LabCenter(Base):
    __tablename__ = "LabCenters"

    LabID = Column(Integer, primary_key=True, index=True)
    Name = Column(String)
    Address = Column(Text)
    Contact = Column(String)
    AccreditationNumber = Column(String)
    ApprovedByAdmin = Column(Boolean, default=False)
    CreatedAt = Column(DateTime, default=datetime.utcnow)
    OwnerUserID = Column(Integer, ForeignKey("Users.UserID"), unique=True, nullable=True)

    owner = relationship("User")
    appointments = relationship("Appointment", back_populates="lab")
    investigation_bookings = relationship("InvestigationBooking", back_populates="lab", cascade="all, delete-orphan")


class Investigation(Base):
    __tablename__ = "Investigations"

    InvestigationID = Column(Integer, primary_key=True, index=True)
    Name = Column(String)
    Description = Column(Text)
    DefaultRate = Column(DECIMAL)

    

class InvestigationBooking(Base):
    __tablename__ = "InvestigationBookings"

    BookingID = Column(Integer, primary_key=True, index=True)
    AppointmentID = Column(Integer, ForeignKey("Appointments.AppointmentID"))
    InvestigationID = Column(Integer, ForeignKey("Investigations.InvestigationID"))
    InvestigationDate = Column(Date)
    LabID = Column(Integer, ForeignKey("LabCenters.LabID"))
    Status = Column(String)
    ResultDate = Column(Date)

    appointment = relationship("Appointment")
    investigation = relationship("Investigation")
    lab = relationship("LabCenter", back_populates="investigation_bookings")
    reports = relationship("Report", back_populates="booking", cascade="all, delete-orphan")
   

    @property
    def InvestigationName(self):
        if self.investigation:
            return self.investigation.Name
        return None

    @property
    def PatientName(self):
        if self.appointment and self.appointment.patient and self.appointment.patient.user:
            user = self.appointment.patient.user
            last_name = f" {user.LastName}" if user.LastName else ""
            return f"{user.FirstName}{last_name}"
        return None

class Report(Base):
    __tablename__ = "Reports"

    ReportID = Column(Integer, primary_key=True, index=True)
    BookingID = Column(Integer, ForeignKey("InvestigationBookings.BookingID"))
    FilePath = Column(Text)
    FileType = Column(String)
    booking = relationship("InvestigationBooking", back_populates="reports")

    @property
    def DocumentID(self):
        return self.ReportID

    @property
    def FileName(self):
        return self.FilePath.rsplit("/", 1)[-1] if self.FilePath else None


# =========================
# 5️⃣  Billing & Payments
# =========================

class Payment(Base):
    __tablename__ = "Payments"

    PaymentID = Column(Integer, primary_key=True, index=True)
    Method = Column(String)
    TransactionRef = Column(String)
    Status = Column(String)
    Date = Column(DateTime, default=datetime.utcnow)


class DoctorBilling(Base):
    __tablename__ = "DoctorBilling"

    DBillID = Column(Integer, primary_key=True, index=True)
    AppointmentID = Column(Integer, ForeignKey("Appointments.AppointmentID"))
    PaymentID = Column(Integer, ForeignKey("Payments.PaymentID"))
    Amount = Column(DECIMAL, nullable=False)
    Date = Column(DateTime, default=datetime.utcnow)

    appointment = relationship("Appointment")
    payment = relationship("Payment")

    @property
    def BillID(self):
        return self.DBillID

    @property
    def BillAmount(self):
        return self.Amount

    @property
    def BillStatus(self):
        return "PAID" if self.PaymentID is not None else "GENERATED"

    @property
    def BillGeneratedAt(self):
        return self.Date

    @property
    def Type(self):
        if self.appointment:
            return self.appointment.Type
        return None

    @property
    def PatientID(self):
        if self.appointment:
            return self.appointment.PatientID
        return None

    @property
    def DoctorID(self):
        if self.appointment:
            return self.appointment.DoctorID
        return None

class LabCenterBilling(Base):
    __tablename__ = "LabCenterBilling"

    LabBillID = Column(Integer, primary_key=True, index=True)
    AppointmentID = Column(Integer, ForeignKey("Appointments.AppointmentID"))
    PaymentID = Column(Integer, ForeignKey("Payments.PaymentID"))
    Amount = Column(DECIMAL, nullable=False)
    Date = Column(DateTime, default=datetime.utcnow)

    appointment = relationship("Appointment")
    payment = relationship("Payment")

    @property
    def BillID(self):
        return self.LabBillID

    @property
    def BillAmount(self):
        return self.Amount

    @property
    def BillStatus(self):
        return "PAID" if self.PaymentID is not None else "GENERATED"

    @property
    def BillGeneratedAt(self):
        return self.Date

    @property
    def AppointmentIDValue(self):
        return self.AppointmentID

    @property
    def LabID(self):
        if self.appointment:
            return self.appointment.LabID
        return None

    @property
    def InvestigationID(self):
        if self.appointment:
            booking = next(iter(getattr(self.appointment, "lab_bookings", []) or []), None)
            if booking:
                return booking.InvestigationID
        return None
