from datetime import datetime

def log(message: str):
    """
    Simple logger utility for UEBA ML module.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[UEBA-ML][{timestamp}] {message}")
