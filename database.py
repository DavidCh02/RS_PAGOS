# database.py
from sqlalchemy import create_engine
from datetime import datetime
import pytz

# Configuración de la base de datos
DATABASE_URL = "postgresql://rstorneos_user:6GWHEnUrLsGv7APN0xr7LQ6clLhr3nwy@dpg-d4ii9ik9c44c73asqqcg-a/rstorneos"
engine = create_engine(DATABASE_URL)

# Función para obtener una conexión a la base de datos
def get_db_connection():
    return engine.connect()

# Obtener la fecha actual en UTC

today_utc = datetime.now(pytz.timezone('UTC')).strftime('%Y-%m-%d')
