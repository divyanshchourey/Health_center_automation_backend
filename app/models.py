from sqlalchemy import (
    Column, Integer, String, Text, Date, DateTime, Boolean, Float, DECIMAL,
    ForeignKey, JSON
)
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

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
    ExperienceYears = Column(Integer)
    ClinicAddress = Column(Text)
    AvailabilitySchedule = Column(JSON)
    AadharNumber = Column(String(12), unique=True)
    PANNumber = Column(String(10), unique=True)
    AccountNumber = Column(String)
    IFSCCode = Column(String)

    user = relationship("User", back_populates="doctor")
    appointments = relationship("Appointment", back_populates="doctor")


class Employee(Base):
    __tablename__ = "Employees"

    EmployeeID = Column(Integer,ForeignKey("Users.UserID"), primary_key=True)
    Division = Column(String)
    Ward = Column(String)
    Designation = Column(String)
    JoinDate = Column(Date)
    Status = Column(String)
    AadharNumber = Column(String(12), unique=True)
    PANNumber = Column(String(10), unique=True)
    AccountNumber = Column(String)
    IFSCCode = Column(String)

    user = relationship("User", back_populates="employee")

# =========================
# 3️⃣  Appointments & Consultations
# =========================

class Appointment(Base):
    __tablename__ = "Appointments"

    AppointmentID = Column(Integer, primary_key=True, index=True)
    PatientID = Column(Integer, ForeignKey("PatientProfiles.PatientID"))
    DoctorID = Column(Integer, ForeignKey("DoctorProfiles.DoctorID"))
    DateTime = Column(DateTime)
    Type = Column(String)
    Status = Column(String)

    patient = relationship("PatientProfile",back_populates="appointments")
    doctor = relationship("DoctorProfile", back_populates="appointments")


class Consultation(Base):
    __tablename__ = "Consultations"

    ConsultationID = Column(Integer, primary_key=True, index=True)
    AppointmentID = Column(Integer, ForeignKey("Appointments.AppointmentID"))
    Notes = Column(Text)
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
    LabID = Column(Integer, ForeignKey("LabCenters.LabID"))
    Status = Column(String)
    ResultDate = Column(Date)

    appointment = relationship("Appointment")
    investigation = relationship("Investigation")
    lab = relationship("LabCenter")


class Report(Base):
    __tablename__ = "Reports"

    ReportID = Column(Integer, primary_key=True, index=True)
    BookingID = Column(Integer, ForeignKey("InvestigationBookings.BookingID"))
    FilePath = Column(Text)
    AbnormalFlag = Column(Boolean)

    booking = relationship("InvestigationBooking")

# =========================
# 5️⃣  Billing & Payments
# =========================

class Discount(Base):
    __tablename__ = "Discounts"

    DiscountID = Column(Integer, primary_key=True, index=True)
    Name = Column(String)
    Rule = Column(JSON)
    StartDate = Column(Date)
    EndDate = Column(Date)
    Percent = Column(Float)


class Payment(Base):
    __tablename__ = "Payments"

    PaymentID = Column(Integer, primary_key=True, index=True)
    Method = Column(String)
    TransactionRef = Column(String)
    Status = Column(String)
    Date = Column(DateTime, default=datetime.utcnow)


class Billing(Base):
    __tablename__ = "Billing"

    BillID = Column(Integer, primary_key=True, index=True)
    AppointmentID = Column(Integer, ForeignKey("Appointments.AppointmentID"))
    PaymentID = Column(Integer, ForeignKey("Payments.PaymentID"))
    DiscountID = Column(Integer, ForeignKey("Discounts.DiscountID"))
    Amount = Column(DECIMAL)
    FinalAmount = Column(DECIMAL)
    Date = Column(DateTime, default=datetime.utcnow)

    appointment = relationship("Appointment")
    payment = relationship("Payment")
    discount = relationship("Discount")

# =========================
# 6️⃣  Attendance
# =========================

class Attendance(Base):
    __tablename__ = "Attendance"

    AttendanceID = Column(Integer, primary_key=True, index=True)
    UserID = Column(Integer, ForeignKey("Users.UserID"))
    Date = Column(Date)
    InTime = Column(DateTime)
    OutTime = Column(DateTime)
    Latitude = Column(Float)
    Longitude = Column(Float)
    Remarks = Column(Text)

    user = relationship("User")
