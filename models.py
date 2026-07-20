def validate_reservation(data):
    service_type = data.get("service_type", "cleaning")
    required_fields = ["user_id", "date", "time_slot"]
    if service_type in ("cleaning", "maintenance_inspection"):
        required_fields += ["longitude", "latitude"]
    if service_type == "cleaning":
        required_fields += ["number_of_panels"]
    for field in required_fields:
        if field not in data:
            return False, f"Missing field: {field}"
    return True, ""
