def success_response(message: str, data=None) -> dict:
    return {"status": "success", "message": message, "data": data}


def error_response(message: str, data=None) -> dict:
    return {"status": "error", "message": message, "data": data}
