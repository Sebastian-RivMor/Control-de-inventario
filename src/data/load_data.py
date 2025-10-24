from src.data.google_loader import get_drive_data

def load_data_from_sheets():
    """Wrapper para mantener compatibilidad con el flujo antiguo."""
    return get_drive_data()
