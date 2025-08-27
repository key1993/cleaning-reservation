def validate_reservation(data):
    required_fields = ["name", "date", "time_slot", "longitude", "latitude", "number_of_panels"]
    for field in required_fields:
        if field not in data:
            return False, f"Missing field: {field}"
    return True, ""
