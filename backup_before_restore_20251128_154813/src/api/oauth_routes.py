# Backward compatibility - реэкспорт из нового расположения
from src.modules.auth.api.oauth_routes import router

__all__ = ["router"]
