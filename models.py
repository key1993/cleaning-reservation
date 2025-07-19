def validate_reservation(data):
    required_fields = ["user_id", "date", "time_slot", "longitude", "altitude", "number_of_panels"]
    for field in required_fields:
        if field not in data:
            return False, f"Missing field: {field}"
    return True, ""
