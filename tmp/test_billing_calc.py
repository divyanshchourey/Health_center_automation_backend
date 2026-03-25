from app.crud.patient import _calculate_doctor_fee

def test_fee_calculation():
    test_cases = [
        ("General Physician", 800.0),
        ("Gynecologist", 1500.0),
        ("Cardiologist", 3000.0),
        ("Dermatologist", 2000.0),
        ("Orthopedic", 1500.0),
        ("Pediatrician", 1200.0),
        ("Psychiatrist", 2500.0),
        ("Unknown", 500.0),
        (None, 500.0),
        ("  General Physician  ", 800.0),
    ]
    
    for spec, expected in test_cases:
        actual = _calculate_doctor_fee(spec)
        assert actual == expected, f"Failed for {spec}: expected {expected}, got {actual}"
    
    print("All fee calculation tests passed!")

if __name__ == "__main__":
    test_fee_calculation()
