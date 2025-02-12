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



@app.route('/pagos', methods=['GET', 'POST'])
def pagos():
    # Fecha predeterminada: hoy
    today = datetime.now().strftime('%Y-%m-%d')
    fecha_seleccionada = today  # Por defecto, usa la fecha actual

    conn = get_db_connection()
    try:
        if request.method == 'POST':
            # Filtrar por fecha seleccionada
            if 'filtrar_fecha' in request.form:
                fecha_seleccionada = request.form.get('fecha_cliente')

            # Actualizar el estado de pago
            elif 'actualizar_pago' in request.form:
                id_pago = int(request.form.get('id_pago'))
                tipo_pago = request.form.get('tipo_pago')  # "tarjeta" o "inscripcion"
                metodo_pago = request.form.get('metodo_pago')
                estado_pago = request.form.get('estado_pago')

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

        # Consultar pagos pendientes para la fecha seleccionada
        result_tarjetas = conn.execute(text("""
            SELECT * FROM pago_tarjetas
            WHERE estado_pago = 'Pendiente' AND fecha_cobro = :fecha
        """), {"fecha": fecha_seleccionada})
        pagos_tarjetas = result_tarjetas.fetchall()

        result_inscripciones = conn.execute(text("""
            SELECT * FROM pago_inscripcion
            WHERE estado_pago = 'Pendiente' AND fecha_inscripcion = :fecha
        """), {"fecha": fecha_seleccionada})
        pagos_inscripciones = result_inscripciones.fetchall()

    finally:
        conn.close()

    return render_template('pagos.html', pagos_tarjetas=pagos_tarjetas, pagos_inscripciones=pagos_inscripciones, fecha_seleccionada=fecha_seleccionada)


# Página para mostrar los pagos realizados hoy
from datetime import datetime
import pytz

@app.route('/pagados_hoy', methods=['GET', 'POST'])
def pagados_hoy():
    if request.method == 'POST':
        # Obtener la fecha enviada por el cliente
        fecha_cliente = request.form.get('fecha_cliente')

        conn = get_db_connection()
        try:
            # Consultar pagos realizados en la fecha del cliente
            result_tarjetas = conn.execute(text("""
                SELECT * FROM pago_tarjetas
                WHERE fecha_cobro = :fecha AND estado_pago = 'Pagado'
            """), {"fecha": fecha_cliente})
            pagos_tarjetas = result_tarjetas.fetchall()

            result_inscripciones = conn.execute(text("""
                SELECT * FROM pago_inscripcion
                WHERE fecha_inscripcion = :fecha AND estado_pago = 'Pagado'
            """), {"fecha": fecha_cliente})
            pagos_inscripciones = result_inscripciones.fetchall()

        finally:
            conn.close()

        return render_template('pagados_hoy.html', pagos_tarjetas=pagos_tarjetas, pagos_inscripciones=pagos_inscripciones)

    return render_template('pagados_hoy.html', pagos_tarjetas=[], pagos_inscripciones=[])


@app.route('/filtrar_pagos', methods=['GET', 'POST'])
def filtrar_pagos():
    if request.method == 'POST':
        fecha = request.form['fecha']
        conn = get_db_connection()
        try:
            # Consultar pagos de tarjetas e inscripciones para la fecha seleccionada
            result_tarjetas = conn.execute(text("""
                SELECT * FROM pago_tarjetas WHERE fecha_cobro = :fecha
            """), {"fecha": fecha})
            pagos_tarjetas = result_tarjetas.fetchall()

            result_inscripciones = conn.execute(text("""
                SELECT * FROM pago_inscripcion WHERE fecha_inscripcion = :fecha
            """), {"fecha": fecha})
            pagos_inscripciones = result_inscripciones.fetchall()

        finally:
            conn.close()

        return render_template('filtrar_pagos.html', pagos_tarjetas=pagos_tarjetas, pagos_inscripciones=pagos_inscripciones, fecha=fecha)

    return render_template('filtrar_pagos.html')

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