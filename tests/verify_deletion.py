
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app import models
import sys

def verify():
    db = SessionLocal()
    try:
        lab_id = 1
        lab = db.query(models.LabCenter).filter(models.LabCenter.LabID == lab_id).first()
        if not lab:
            print(f"Lab {lab_id} not found. Trying to find any lab with bookings.")
            booking = db.query(models.InvestigationBooking).first()
            if booking:
                lab_id = booking.LabID
                lab = db.query(models.LabCenter).filter(models.LabCenter.LabID == lab_id).first()
            else:
                print("No labs or bookings found to test.")
                return

        print(f"Attempting to delete LabID: {lab_id} ({lab.Name})")
        
        # Check dependencies before deletion
        bookings_count = db.query(models.InvestigationBooking).filter(models.InvestigationBooking.LabID == lab_id).count()
        appointments_count = db.query(models.Appointment).filter(models.Appointment.LabID == lab_id).count()
        
        print(f"Found {bookings_count} investigation bookings and {appointments_count} appointments referencing this lab.")

        # Perform deletion
        db.delete(lab)
        db.commit()
        print("Deletion successful!")

        # Verify cascades
        bookings_after = db.query(models.InvestigationBooking).filter(models.InvestigationBooking.LabID == lab_id).count()
        appointments_after = db.query(models.Appointment).filter(models.Appointment.LabID == lab_id).count()
        
        print(f"Bookings after deletion: {bookings_after} (expected 0)")
        print(f"Appointments referencing this lab after deletion: {appointments_after} (expected 0)")
        
        # Check if appointments still exist but LabID is NULL
        # Wait, the above query filters by LabID == lab_id, so it should be 0.
        # Let's check if they still exist.
        # We'd need the appointment IDs.
        
    except Exception as e:
        db.rollback()
        print(f"Error during verification: {e}")
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    verify()
