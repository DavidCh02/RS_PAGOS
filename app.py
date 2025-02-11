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

# Página de pagos del día actual
# Página de pagos del día actual
@app.route('/pagos', methods=['GET', 'POST'])
def pagos():
    today = datetime.today().strftime('%Y-%m-%d')
    conn = get_db_connection()
    try:
        if request.method == 'POST':
            # Actualizar el método de pago y estado de pago
            id_pago = int(request.form['id_pago'])
            tipo_pago = request.form['tipo_pago']  # 'tarjeta' o 'inscripcion'
            metodo_pago = request.form['metodo_pago']
            estado_pago = request.form['estado_pago']

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
            conn.commit()  # Confirmar los cambios

        # Consultar pagos pendientes de hoy
        result_tarjetas = conn.execute(text("""
            SELECT * FROM pago_tarjetas WHERE fecha_cobro = :fecha AND estado_pago = 'Pendiente'
        """), {"fecha": today})
        pagos_tarjetas = result_tarjetas.fetchall()

        result_inscripciones = conn.execute(text("""
            SELECT * FROM pago_inscripcion WHERE fecha_inscripcion = :fecha AND estado_pago = 'Pendiente'
        """), {"fecha": today})
        pagos_inscripciones = result_inscripciones.fetchall()

    finally:
        conn.close()

    return render_template('pagos.html', pagos_tarjetas=pagos_tarjetas, pagos_inscripciones=pagos_inscripciones)

# Página para mostrar los pagos realizados hoy
@app.route('/pagados_hoy', methods=['GET', 'POST'])
def pagados_hoy():
    today = datetime.today().strftime('%Y-%m-%d')
    conn = get_db_connection()
    try:
        # Consultar pagos realizados hoy
        result_tarjetas = conn.execute(text("""
            SELECT * FROM pago_tarjetas WHERE fecha_cobro = :fecha AND estado_pago = 'Pagado'
        """), {"fecha": today})
        pagos_tarjetas = result_tarjetas.fetchall()

        result_inscripciones = conn.execute(text("""
            SELECT * FROM pago_inscripcion WHERE fecha_inscripcion = :fecha AND estado_pago = 'Pagado'
        """), {"fecha": today})
        pagos_inscripciones = result_inscripciones.fetchall()

    finally:
        conn.close()

    return render_template('pagados_hoy.html', pagos_tarjetas=pagos_tarjetas, pagos_inscripciones=pagos_inscripciones)

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