from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash
from sqlalchemy import create_engine, text

# Crear la aplicación Flask
app = Flask(__name__)
app.secret_key = "supersecretkey"  # Clave secreta para usar flash()

# Configuración de la base de datos
DATABASE_URL = "postgresql+pg8000://cobros_db_user:fVyfuaAwHrxz0HhIWKLZTviMvcGUATI0@dpg-culnd35umphs73f086ug-a.oregon-postgres.render.com/cobros_db"
engine = create_engine(DATABASE_URL)

# Función auxiliar para obtener una conexión a la base de datos
def get_db_connection():
    return engine.connect()


from datetime import datetime
import pytz

# Obtener la fecha actual en UTC
timezone = pytz.timezone('UTC')
today_utc = datetime.now(timezone).strftime('%Y-%m-%d')  # Fecha actual en UTC


# Ruta principal
@app.route('/')
def index():
    return redirect(url_for('admin'))

# Panel de administrador
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        conn = get_db_connection()
        try:
            # Agregar pago de tarjetas
            if 'agregar_tarjeta' in request.form:
                numero_partido_jugado = int(request.form['numero_partido_jugado'])
                fecha_cobro = request.form['fecha_cobro']
                jugador = request.form['jugador']
                categoria = request.form['categoria']
                tarjetas_rojas = int(request.form['tarjetas_rojas'])
                tarjetas_amarillas = int(request.form['tarjetas_amarillas'])
                observaciones = request.form['observaciones']

                conn.execute(text("""
                    INSERT INTO pago_tarjetas (
                        numero_partido_jugado, fecha_cobro, jugador, categoria,
                        tarjetas_rojas, tarjetas_amarillas, observaciones, estado_pago, metodo_pago
                    ) VALUES (:numero_partido_jugado, :fecha_cobro, :jugador, :categoria,
                              :tarjetas_rojas, :tarjetas_amarillas, :observaciones, :estado_pago, :metodo_pago)
                """), {
                    "numero_partido_jugado": numero_partido_jugado,
                    "fecha_cobro": fecha_cobro,
                    "jugador": jugador,
                    "categoria": categoria,
                    "tarjetas_rojas": tarjetas_rojas,
                    "tarjetas_amarillas": tarjetas_amarillas,
                    "observaciones": observaciones,
                    "estado_pago": "Pendiente",
                    "metodo_pago": "Pendiente"
                })
                conn.commit()  # Confirmar los cambios

            # Agregar pago de inscripción
            # Agregar pago de inscripción
            elif 'agregar_inscripcion' in request.form:
                equipo = request.form['equipo']
                jugador = request.form['jugador']
                categoria = request.form['categoria']
                fecha_inscripcion = request.form['fecha_inscripcion']
                monto_a_cobrar = float(request.form['monto_a_cobrar'])
                metodo_pago = request.form['metodo_pago']  # Nuevo campo
                observaciones = request.form['observaciones']

                conn.execute(text("""
                    INSERT INTO pago_inscripcion (
                        equipo, jugador, categoria, fecha_inscripcion, monto_a_cobrar, metodo_pago, observaciones, estado_pago
                    ) VALUES (:equipo, :jugador, :categoria, :fecha_inscripcion, :monto_a_cobrar, :metodo_pago, :observaciones, :estado_pago)
                """), {
                    "equipo": equipo,
                    "jugador": jugador,
                    "categoria": categoria,
                    "fecha_inscripcion": fecha_inscripcion,
                    "monto_a_cobrar": monto_a_cobrar,
                    "metodo_pago": metodo_pago,
                    "observaciones": observaciones,
                    "estado_pago": "Pendiente"  # Estado inicial
                })
                conn.commit()  # Confirmar los cambios

        finally:
            conn.close()

        return redirect(url_for('admin'))

    return render_template('admin.html')


from datetime import datetime, timedelta
import pytz

from datetime import datetime, timedelta
import pytz

from flask import request, redirect, url_for

@app.route('/pagos', methods=['GET', 'POST'])
def pagos():
    # Obtener la fecha actual en UTC
    timezone = pytz.timezone('UTC')
    today_utc = datetime.now(timezone).date()

    # Calcular el inicio y fin de la semana actual (lunes a domingo)
    start_of_week = today_utc - timedelta(days=today_utc.weekday())  # Lunes
    end_of_week = start_of_week + timedelta(days=6)  # Domingo

    # Calcular las fechas específicas para sábado y domingo
    sabado = start_of_week + timedelta(days=5)  # Sábado
    domingo = start_of_week + timedelta(days=6)  # Domingo

    conn = get_db_connection()
    try:
        if request.method == 'POST':
            # Actualizar el estado de pago
            if 'actualizar_pago' in request.form:
                id_pago = request.form.get('id_pago')  # Obtener el ID del pago
                tipo_pago = request.form.get('tipo_pago')  # "tarjeta" o "inscripcion"
                metodo_pago = request.form.get('metodo_pago')
                estado_pago = request.form.get('estado_pago')

                # Validar que los campos no estén vacíos
                if not id_pago or not tipo_pago or not metodo_pago or not estado_pago:
                    return "Error: Todos los campos son obligatorios.", 400

                try:
                    id_pago = int(id_pago)  # Convertir a entero
                except ValueError:
                    return "Error: ID de pago inválido.", 400

                # Actualizar el estado del pago en la base de datos
                if tipo_pago == 'tarjeta':
                    conn.execute(text("""
                        UPDATE pago_tarjetas
                        SET metodo_pago = :metodo_pago, estado_pago = :estado_pago
                        WHERE id_pago = :id_pago
                    """), {
                        "id_pago": id_pago,
                        "metodo_pago": metodo_pago,
                        "estado_pago": estado_pago
                    })
                elif tipo_pago == 'inscripcion':
                    conn.execute(text("""
                        UPDATE pago_inscripcion
                        SET metodo_pago = :metodo_pago, estado_pago = :estado_pago
                        WHERE id_inscripcion = :id_pago
                    """), {
                        "id_pago": id_pago,
                        "metodo_pago": metodo_pago,
                        "estado_pago": estado_pago
                    })
                conn.commit()

                # Redirigir para evitar problemas con el formulario POST
                return redirect(url_for('pagos'))

        # Consultar pagos pendientes de sábado y domingo de la semana actual
        result_tarjetas = conn.execute(text("""
            SELECT *
            FROM pago_tarjetas
            WHERE estado_pago = 'Pendiente'
              AND EXTRACT(DOW FROM fecha_cobro) IN (0, 6)  -- Domingo (0) y Sábado (6)
              AND fecha_cobro BETWEEN :start_of_week AND :end_of_week
        """), {"start_of_week": start_of_week, "end_of_week": end_of_week})
        pagos_tarjetas = result_tarjetas.fetchall()

        result_inscripciones = conn.execute(text("""
            SELECT *
            FROM pago_inscripcion
            WHERE estado_pago = 'Pendiente'
              AND EXTRACT(DOW FROM fecha_inscripcion) IN (0, 6)  -- Domingo (0) y Sábado (6)
              AND fecha_inscripcion BETWEEN :start_of_week AND :end_of_week
        """), {"start_of_week": start_of_week, "end_of_week": end_of_week})
        pagos_inscripciones = result_inscripciones.fetchall()

    finally:
        conn.close()

    # Mapear números de día de la semana a nombres
    dias_semana = {0: "Domingo", 6: "Sábado"}

    # Agrupar pagos por día de la semana
    pagos_por_dia = {dia: {"tarjetas": [], "inscripciones": []} for dia in dias_semana.values()}

    for pago in pagos_tarjetas:
        dia_nombre = dias_semana[int(pago.fecha_cobro.isoweekday() % 7)]  # Convertir ISO weekday a DOW
        pagos_por_dia[dia_nombre]["tarjetas"].append(pago)

    for pago in pagos_inscripciones:
        dia_nombre = dias_semana[int(pago.fecha_inscripcion.isoweekday() % 7)]  # Convertir ISO weekday a DOW
        pagos_por_dia[dia_nombre]["inscripciones"].append(pago)

    # Pasar las fechas calculadas a la plantilla
    return render_template(
        'pagos.html',
        pagos_por_dia=pagos_por_dia,
        fecha_actual=today_utc,
        fecha_sabado=sabado,
        fecha_domingo=domingo
    )


# Página para mostrar los pagos realizados hoy
from datetime import datetime
import pytz

from datetime import datetime, timedelta
import pytz

from datetime import datetime, timedelta
import pytz

from datetime import datetime, timedelta
import pytz
from datetime import datetime, timedelta
import pytz

from datetime import datetime, timedelta
import pytz

@app.route('/pagados_hoy', methods=['GET'])
def pagados_hoy():
    # Obtener la fecha actual en la zona horaria local (por ejemplo, 'America/Bogota')
    timezone = pytz.timezone('America/Bogota')  # Cambia esto a tu zona horaria
    today_local = datetime.now(timezone).date()

    # Calcular el inicio y fin de la semana actual (lunes a domingo) en la zona horaria local
    start_of_week = today_local - timedelta(days=today_local.weekday())  # Lunes
    end_of_week = start_of_week + timedelta(days=6)  # Domingo

    conn = get_db_connection()
    try:
        # Consultar pagos realizados en la semana actual
        result_tarjetas = conn.execute(text("""
            SELECT *, fecha_cobro AT TIME ZONE 'UTC' AT TIME ZONE :timezone AS fecha_cobro_local
            FROM pago_tarjetas
            WHERE estado_pago = 'Pagado' AND fecha_cobro BETWEEN :start_of_week AND :end_of_week
        """), {"start_of_week": start_of_week, "end_of_week": end_of_week, "timezone": timezone.zone})
        pagos_tarjetas = result_tarjetas.fetchall()

        result_inscripciones = conn.execute(text("""
            SELECT *, fecha_inscripcion AT TIME ZONE 'UTC' AT TIME ZONE :timezone AS fecha_inscripcion_local
            FROM pago_inscripcion
            WHERE estado_pago = 'Pagado' AND fecha_inscripcion BETWEEN :start_of_week AND :end_of_week
        """), {"start_of_week": start_of_week, "end_of_week": end_of_week, "timezone": timezone.zone})
        pagos_inscripciones = result_inscripciones.fetchall()

    finally:
        conn.close()

    # Mapear números de día de la semana a nombres
    dias_semana = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]

    # Agrupar pagos por día de la semana
    pagos_por_dia = {}

    for pago in pagos_tarjetas + pagos_inscripciones:
        # Obtener la fecha del pago en la zona horaria local
        if hasattr(pago, "fecha_cobro_local"):
            fecha_pago_local = pago.fecha_cobro_local.date()  # Convertir a date si es necesario
        elif hasattr(pago, "fecha_inscripcion_local"):
            fecha_pago_local = pago.fecha_inscripcion_local.date()  # Convertir a date si es necesario

        # Obtener el número del día de la semana (0 = Lunes, 1 = Martes, ..., 6 = Domingo)
        numero_dia_semana = fecha_pago_local.weekday()

        # Convertir el número del día de la semana a nombre
        dia_nombre = dias_semana[numero_dia_semana]

        # Agregar el pago al grupo correspondiente
        if dia_nombre not in pagos_por_dia:
            pagos_por_dia[dia_nombre] = {"tarjetas": [], "inscripciones": []}
        if hasattr(pago, "fecha_cobro_local"):
            pagos_por_dia[dia_nombre]["tarjetas"].append(pago)
        elif hasattr(pago, "fecha_inscripcion_local"):
            pagos_por_dia[dia_nombre]["inscripciones"].append(pago)

    # Filtrar días sin pagos
    pagos_por_dia = {dia: pagos for dia, pagos in pagos_por_dia.items() if pagos["tarjetas"] or pagos["inscripciones"]}

    # Calcular los nombres de los días de la semana para el rango de fechas
    start_of_week_nombre = dias_semana[start_of_week.weekday()]
    end_of_week_nombre = dias_semana[end_of_week.weekday()]

    return render_template(
        'pagados_hoy.html',
        pagos_por_dia=pagos_por_dia,
        start_of_week=start_of_week,
        end_of_week=end_of_week,
        start_of_week_nombre=start_of_week_nombre,
        end_of_week_nombre=end_of_week_nombre
    )

@app.route('/filtrar_pagos', methods=['GET', 'POST'])
def filtrar_pagos():
    fecha_seleccionada = None
    pagos_tarjetas = []
    pagos_inscripciones = []

    conn = get_db_connection()
    try:
        if request.method == 'POST':
            fecha_seleccionada = request.form.get('fecha_cliente')

            # Consultar pagos para la fecha seleccionada
            result_tarjetas = conn.execute(text("""
                SELECT *, EXTRACT(DOW FROM fecha_cobro) AS dia_semana
                FROM pago_tarjetas
                WHERE fecha_cobro = :fecha
            """), {"fecha": fecha_seleccionada})

            # Convertir los resultados en diccionarios manualmente
            pagos_tarjetas = [
                {
                    "id_pago": row.id_pago,
                    "numero_partido_jugado": row.numero_partido_jugado,
                    "fecha_cobro": row.fecha_cobro,
                    "jugador": row.jugador,
                    "categoria": row.categoria,
                    "tarjetas_rojas": row.tarjetas_rojas,
                    "tarjetas_amarillas": row.tarjetas_amarillas,
                    "valor_total_pagar": row.valor_total_pagar,
                    "observaciones": row.observaciones,
                    "estado_pago": row.estado_pago,
                    "metodo_pago": row.metodo_pago,
                    "dia_semana": int(row.dia_semana)
                }
                for row in result_tarjetas.fetchall()
            ]

            result_inscripciones = conn.execute(text("""
                SELECT *, EXTRACT(DOW FROM fecha_inscripcion) AS dia_semana
                FROM pago_inscripcion
                WHERE fecha_inscripcion = :fecha
            """), {"fecha": fecha_seleccionada})

            # Convertir los resultados en diccionarios manualmente
            pagos_inscripciones = [
                {
                    "id_inscripcion": row.id_inscripcion,
                    "equipo": row.equipo,
                    "jugador": row.jugador,
                    "categoria": row.categoria,
                    "fecha_inscripcion": row.fecha_inscripcion,
                    "monto_a_cobrar": row.monto_a_cobrar,
                    "observaciones": row.observaciones,
                    "estado_pago": row.estado_pago,
                    "metodo_pago": row.metodo_pago,
                    "dia_semana": int(row.dia_semana)
                }
                for row in result_inscripciones.fetchall()
            ]

    finally:
        conn.close()

    # Mapear números de día de la semana a nombres
    dias_semana = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]

    # Agregar el nombre del día de la semana a cada pago
    for pago in pagos_tarjetas:
        pago['dia_nombre'] = dias_semana[pago['dia_semana']]

    for pago in pagos_inscripciones:
        pago['dia_nombre'] = dias_semana[pago['dia_semana']]

    return render_template(
        'filtrar_pagos.html',
        pagos_tarjetas=pagos_tarjetas,
        pagos_inscripciones=pagos_inscripciones,
        fecha_seleccionada=fecha_seleccionada
    )


if __name__ == '__main__':
    app.run(debug=True)


    @app.route('/debug-time')
    def debug_time():
        from datetime import datetime
        import pytz

        # Fecha y hora del servidor en UTC
        server_time_utc = datetime.now(pytz.timezone('UTC')).strftime('%Y-%m-%d %H:%M:%S')

        # Fecha y hora del servidor en tu zona horaria (UTC-5)
        server_time_local = datetime.now(pytz.timezone('America/Bogota')).strftime('%Y-%m-%d %H:%M:%S')

        return f"Server Time (UTC): {server_time_utc}<br>Server Time (Local): {server_time_local}"