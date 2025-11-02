import sys
from pathlib import Path

# Aggiungi la directory menu_service al path per gli import
menu_service_dir = Path(__file__).parent.parent
sys.path.insert(0, str(menu_service_dir))

