# Backward compatibility - реэкспорт из нового расположения
# Dashboard v2 Module перенесен в src/modules/dashboard/
from src.modules.dashboard.api.dashboard_v2 import router

__all__ = ["router"]
