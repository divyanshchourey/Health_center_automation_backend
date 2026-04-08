import sys
from decimal import Decimal
from unittest.mock import MagicMock

# Mocking app.models and app.schemas for the test
sys.modules['app'] = MagicMock()
sys.modules['app.models'] = MagicMock()
sys.modules['app.schemas'] = MagicMock()
sys.modules['app.crud.profile_image'] = MagicMock()

# Import the functions to test
# We need to set up the environment so it can find the code
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.crud.employee import _normalize_checkup_category, DOCTOR_CHECKUP_PRICING, generate_doctor_bill

def test_normalization():
    print("Testing normalization...")
    assert _normalize_checkup_category("Orthopedic") == "orthopedic"
    assert _normalize_checkup_category("General Physician") == "general_physician"
    assert _normalize_checkup_category("consultation") == "consultation"
    assert _normalize_checkup_category("") == "others"
    assert _normalize_checkup_category(None) == "others"
    
    try:
        _normalize_checkup_category("Brain Surgeon")
        assert False, "Should have raised ValueError"
    except ValueError as e:
        print(f"Caught expected error: {e}")

    print("Normalization tests passed!")

def test_billing_logic():
    print("\nTesting billing logic...")
    db = MagicMock()
    
    # Mock Appointment
    appointment = MagicMock()
    appointment.AppointmentID = 1
    appointment.Type = "Orthopedic"
    
    db.query().filter().first.return_value = appointment # for appointment check
    db.query().filter().first.side_effect = [appointment, None] # 1st for appointment, 2nd for existing bill check
    
    bill = generate_doctor_bill(db, 1)
    
    print(f"Calculated Amount for Orthopedic: {bill.Amount}")
    assert bill.Amount == Decimal("1500.00")
    # Verify Type preservation for specializations
    assert appointment.Type == "Orthopedic"
    
    # Test core type normalization
    appointment.Type = "consultation"
    db.query().filter().first.side_effect = [appointment, None]
    bill = generate_doctor_bill(db, 1)
    print(f"Calculated Amount for consultation: {bill.Amount}")
    assert bill.Amount == Decimal("800.00")
    assert appointment.Type == "consultation"

    print("Billing logic tests passed!")

if __name__ == "__main__":
    test_normalization()
    test_billing_logic()
