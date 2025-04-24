# database.py
from sqlalchemy import create_engine
from datetime import datetime
import pytz

# Configuración de la base de datos
DATABASE_URL = "postgresql+pg8000://rs_pagos_user:XnBxCpRwG7C4Cb6jKIzZ2Wta3NJoOdfI@dpg-cvrlids9c44c73d6113g-a.oregon-postgres.render.com/rs_pagos"
engine = create_engine(DATABASE_URL)

# Función para obtener una conexión a la base de datos
def get_db_connection():
    return engine.connect()

# Obtener la fecha actual en UTC
today_utc = datetime.now(pytz.timezone('UTC')).strftime('%Y-%m-%d')