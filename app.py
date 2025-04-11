from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash
from sqlalchemy import create_engine, text
from flask import Flask, request, jsonify

# Crear la aplicación Flask
app = Flask(__name__)
app.secret_key = "supersecretkey"  # Clave secreta para usar flash()

if __name__ == '__main__':
    app.run(debug=True)


# Configuración de la base de datos
DATABASE_URL = "postgresql+pg8000://rs_pagos_user:XnBxCpRwG7C4Cb6jKIzZ2Wta3NJoOdfI@dpg-cvrlids9c44c73d6113g-a.oregon-postgres.render.com/rs_pagos"
engine = create_engine(DATABASE_URL)


# Función auxiliar para obtener una conexión a la base de datos
def get_db_connection():
    return engine.connect()


from datetime import datetime
import pytz

# Obtener la fecha actual en UTC
timezone = pytz.timezone('UTC')
today_utc = datetime.now(timezone).strftime('%Y-%m-%d')  # Fecha actual en UTC


# Ruta para procesar envíos por lotes
@app.route('/admin/batch', methods=['POST'])
def process_batch():
    conn = get_db_connection()
    try:
        data = request.get_json()
        
        # Validar datos requeridos
        if not data or 'jugadores' not in data or not data['jugadores']:
            return jsonify({"success": False, "message": "No se proporcionaron datos de jugadores."})

        # Manejar el equipo (existente o nuevo)
        equipo_id = data.get('equipo_id')
        if not equipo_id and data.get('nuevo_equipo'):
            result = conn.execute(text("""
                INSERT INTO equipo_pagos (nombre_equipo)
                VALUES (:nombre_equipo)
                RETURNING id_equipo
            """), {"nombre_equipo": data['nuevo_equipo']})
            equipo_id = result.fetchone()[0]
        elif equipo_id:
            equipo_id = int(equipo_id)
        else:
            return jsonify({"success": False, "message": "Debes seleccionar un equipo existente o ingresar uno nuevo."})

        # Procesar cada jugador
        for jugador in data['jugadores']:
            if 'fecha_cobro' in data:  # Procesar tarjetas
                conn.execute(text("""
                    INSERT INTO pago_tarjetas (
                        id_equipo, numero_partido_jugado, fecha_cobro,
                        jugador, categoria, tarjetas_rojas,
                        tarjetas_amarillas, observaciones, estado_pago
                    ) VALUES (
                        :id_equipo, :numero_partido_jugado, :fecha_cobro,
                        :jugador, :categoria, :tarjetas_rojas,
                        :tarjetas_amarillas, :observaciones, :estado_pago
                    )
                """), {
                    "id_equipo": equipo_id,
                    "numero_partido_jugado": data['numero_partido_jugado'],
                    "fecha_cobro": data['fecha_cobro'],
                    "jugador": jugador['nombre'],
                    "categoria": data['categoria'],
                    "tarjetas_rojas": int(jugador.get('tarjetas_rojas', 0)),
                    "tarjetas_amarillas": int(jugador.get('tarjetas_amarillas', 0)),
                    "observaciones": jugador.get('observaciones', ''),
                    "estado_pago": "Pendiente"
                })
            else:  # Procesar inscripciones
                conn.execute(text("""
                    INSERT INTO pago_inscripcion (
                        id_equipo, jugador, categoria, fecha_inscripcion,
                        monto_a_cobrar, metodo_pago, observaciones, estado_pago
                    ) VALUES (
                        :id_equipo, :jugador, :categoria, :fecha_inscripcion,
                        :monto_a_cobrar, :metodo_pago, :observaciones, :estado_pago
                    )
                """), {
                    "id_equipo": equipo_id,
                    "jugador": jugador['nombre'],
                    "categoria": data['categoria'],
                    "fecha_inscripcion": data['fecha_inscripcion'],
                    "monto_a_cobrar": float(data['monto_a_cobrar']),
                    "metodo_pago": data['metodo_pago'],
                    "observaciones": jugador.get('observaciones', ''),
                    "estado_pago": "Pendiente"
                })

        conn.commit()
        return jsonify({"success": True, "message": "Datos agregados correctamente."})

    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "message": str(e)})
    finally:
        conn.close()

# Ruta principal
@app.route('/')
def index():
    return redirect(url_for('admin'))


# Panel de administrador
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    # Obtener lista de equipos existentes
    conn = get_db_connection()
    try:
        result_equipos = conn.execute(text("SELECT id_equipo, nombre_equipo FROM equipo_pagos"))
        equipos_existentes = {row.id_equipo: row.nombre_equipo for row in result_equipos.fetchall()}
    finally:
        conn.close()

    if request.method == 'POST':
        conn = get_db_connection()
        try:
            # Agregar pago de inscripción
            if 'agregar_inscripcion' in request.form:
                equipo_id = request.form.get('equipo_id')  # ID del equipo seleccionado o nuevo
                jugador = request.form['jugador']
                categoria = request.form['categoria']
                fecha_inscripcion = request.form['fecha_inscripcion']
                monto_a_cobrar = float(request.form['monto_a_cobrar'])
                metodo_pago = request.form['metodo_pago']
                observaciones = request.form['observaciones']

                # Manejar el caso de "nuevo equipo"
                if not equipo_id and request.form.get('nuevo_equipo'):
                    # Si el equipo no existe, agregarlo a la tabla equipo_pagos
                    result = conn.execute(text("""
                                INSERT INTO equipo_pagos (nombre_equipo)
                                VALUES (:nombre_equipo)
                                RETURNING id_equipo
                            """), {"nombre_equipo": request.form['nuevo_equipo']})
                    equipo_id = result.fetchone()[0]  # Obtener el ID del nuevo equipo
                elif equipo_id:
                    equipo_id = int(equipo_id)  # Convertir a entero si no es None
                else:
                    return jsonify(
                        {"success": False, "message": "Debes seleccionar un equipo existente o ingresar uno nuevo."})

                # Insertar el pago de inscripción con el ID del equipo
                conn.execute(text("""
                            INSERT INTO pago_inscripcion (
                                id_equipo, jugador, categoria, fecha_inscripcion,
                                monto_a_cobrar, metodo_pago, observaciones, estado_pago
                            ) VALUES (:id_equipo, :jugador, :categoria, :fecha_inscripcion,
                                      :monto_a_cobrar, :metodo_pago, :observaciones, :estado_pago)
                        """), {
                    "id_equipo": equipo_id,
                    "jugador": jugador,
                    "categoria": categoria,
                    "fecha_inscripcion": fecha_inscripcion,
                    "monto_a_cobrar": monto_a_cobrar,
                    "metodo_pago": metodo_pago,
                    "observaciones": observaciones,
                    "estado_pago": "Pendiente"
                })
                conn.commit()  # Confirmar los cambios

            # Agregar pago de tarjetas
            elif 'agregar_tarjeta' in request.form:
                numero_partido_jugado = request.form['numero_partido_jugado']  # Remove the int() conversion
                fecha_cobro = request.form['fecha_cobro']
                jugador = request.form['jugador']
                categoria = request.form['categoria']
                tarjetas_rojas = int(request.form['tarjetas_rojas'])
                tarjetas_amarillas = int(request.form['tarjetas_amarillas'])
                observaciones = request.form['observaciones']
                equipo_id = request.form.get('equipo_id')  # Nuevo campo para el equipo

                # Manejar el caso de "nuevo equipo"
                if not equipo_id and request.form.get('nuevo_equipo'):
                    result = conn.execute(text("""
                                INSERT INTO equipo_pagos (nombre_equipo)
                                VALUES (:nombre_equipo)
                                RETURNING id_equipo
                            """), {"nombre_equipo": request.form['nuevo_equipo']})
                    equipo_id = result.fetchone()[0]  # Obtener el ID del nuevo equipo
                elif equipo_id:
                    equipo_id = int(equipo_id)  # Convertir a entero si no es None
                else:
                    return jsonify(
                        {"success": False, "message": "Debes seleccionar un equipo existente o ingresar uno nuevo."})

                # Insertar el pago de tarjetas con el ID del equipo
                conn.execute(text("""
                    INSERT INTO pago_tarjetas (
                        numero_partido_jugado, fecha_cobro, jugador, categoria,
                        tarjetas_rojas, tarjetas_amarillas, observaciones, estado_pago, metodo_pago, id_equipo
                    ) VALUES (:numero_partido_jugado, :fecha_cobro, :jugador, :categoria,
                              :tarjetas_rojas, :tarjetas_amarillas, :observaciones, :estado_pago, :metodo_pago, :id_equipo)
                """), {
                    "numero_partido_jugado": numero_partido_jugado,
                    "fecha_cobro": fecha_cobro,
                    "jugador": jugador,
                    "categoria": categoria,
                    "tarjetas_rojas": tarjetas_rojas,
                    "tarjetas_amarillas": tarjetas_amarillas,
                    "observaciones": observaciones,
                    "estado_pago": "Pendiente",
                    "metodo_pago": "Pendiente",
                    "id_equipo": equipo_id
                })
                conn.commit()  # Confirmar los cambios

            # Devolver una respuesta JSON para el frontend
            return jsonify({
                "success": True,
                "message": "Datos agregados correctamente."
            })

        except Exception as e:
            conn.rollback()
            print(f"Error detallado: {str(e)}")  # Imprime el error en la terminal
            return jsonify({"success": False, "message": f"Error al procesar la solicitud: {str(e)}"})
        finally:
            conn.close()

    # Renderizar la plantilla con la lista de equipos existentes
    return render_template('admin.html', equipos_existentes=equipos_existentes)


if __name__ == '__main__':
    app.run(debug=True)

from flask import request, redirect, url_for

from datetime import datetime, timedelta
import pytz
from flask import request, redirect, url_for, render_template
from sqlalchemy import text


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

                conn.commit()  # Confirmar los cambios
                return redirect(url_for('pagos'))  # Redirigir para evitar problemas con el formulario POST

        # Consultar pagos pendientes de sábado y domingo de la semana actual
        result_tarjetas = conn.execute(text("""
            SELECT pt.*, ep.nombre_equipo
            FROM pago_tarjetas pt
            LEFT JOIN equipo_pagos ep ON pt.id_equipo = ep.id_equipo
            WHERE pt.estado_pago = 'Pendiente'
              AND EXTRACT(DOW FROM pt.fecha_cobro) IN (0, 6)  -- Domingo (0) y Sábado (6)
              AND pt.fecha_cobro BETWEEN :start_of_week AND :end_of_week
        """), {"start_of_week": start_of_week, "end_of_week": end_of_week})
        pagos_tarjetas = result_tarjetas.fetchall()

        result_inscripciones = conn.execute(text("""
            SELECT pi.*, ep.nombre_equipo
            FROM pago_inscripcion pi
            LEFT JOIN equipo_pagos ep ON pi.id_equipo = ep.id_equipo
            WHERE pi.estado_pago = 'Pendiente'
              AND EXTRACT(DOW FROM pi.fecha_inscripcion) IN (0, 6)
              AND pi.fecha_inscripcion BETWEEN :start_of_week AND :end_of_week
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
    global fecha_pago_local
    timezone = pytz.timezone('America/Bogota')  # Cambia esto a tu zona horaria
    today_local = datetime.now(timezone).date()

    # Calcular el inicio y fin de la semana actual (lunes a domingo) en la zona horaria local
    start_of_week = today_local - timedelta(days=today_local.weekday())  # Lunes
    end_of_week = start_of_week + timedelta(days=6)  # Domingo

    conn = get_db_connection()
    try:
        # Consultar pagos realizados en la semana actual (Tarjetas)
        result_tarjetas = conn.execute(text("""
            SELECT pt.*, 
                   ep.nombre_equipo, 
                   fecha_cobro AT TIME ZONE 'UTC' AT TIME ZONE :timezone AS fecha_cobro_local
            FROM pago_tarjetas pt
            LEFT JOIN equipo_pagos ep ON pt.id_equipo = ep.id_equipo
            WHERE pt.estado_pago = 'Pagado' AND pt.fecha_cobro BETWEEN :start_of_week AND :end_of_week
        """), {"start_of_week": start_of_week, "end_of_week": end_of_week, "timezone": timezone.zone})
        pagos_tarjetas = result_tarjetas.fetchall()

        # Consultar pagos realizados en la semana actual (Inscripciones)
        result_inscripciones = conn.execute(text("""
            SELECT pi.*, 
                   ep.nombre_equipo, 
                   fecha_inscripcion AT TIME ZONE 'UTC' AT TIME ZONE :timezone AS fecha_inscripcion_local
            FROM pago_inscripcion pi
            LEFT JOIN equipo_pagos ep ON pi.id_equipo = ep.id_equipo
            WHERE pi.estado_pago = 'Pagado' AND pi.fecha_inscripcion BETWEEN :start_of_week AND :end_of_week
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
    numero_partido = None
    estado_seleccionado = None
    pagos_tarjetas = []
    pagos_inscripciones = []
    equipos_existentes = {}

    conn = get_db_connection()
    try:
        # ✅ Cargar equipos desde la base de datos
        result_equipos = conn.execute(text("SELECT id_equipo, nombre_equipo FROM equipo_pagos"))
        equipos_existentes = {row.id_equipo: row.nombre_equipo for row in result_equipos.fetchall()}

        if request.method == 'POST':
            tipo_busqueda = request.form.get('tipo_busqueda')
            estado_seleccionado = request.form.get('estado_pago')

            # Base queries
            query_tarjetas = """
                SELECT pt.*, ep.nombre_equipo
                FROM pago_tarjetas pt
                LEFT JOIN equipo_pagos ep ON pt.id_equipo = ep.id_equipo
                WHERE 1=1
            """
            query_inscripciones = """
                SELECT pi.*, ep.nombre_equipo
                FROM pago_inscripcion pi
                LEFT JOIN equipo_pagos ep ON pi.id_equipo = ep.id_equipo
                WHERE 1=1
            """

            params_tarjetas = {}
            params_inscripciones = {}

            if tipo_busqueda == 'fecha':
                fecha_seleccionada = request.form.get('fecha_cliente')
                if fecha_seleccionada:
                    query_tarjetas += " AND pt.fecha_cobro = :fecha"
                    query_inscripciones += " AND pi.fecha_inscripcion = :fecha"
                    params_tarjetas["fecha"] = fecha_seleccionada
                    params_inscripciones["fecha"] = fecha_seleccionada
            else:
                numero_partido = request.form.get('numero_partido')
                if numero_partido:
                    query_tarjetas += " AND pt.numero_partido_jugado = :numero_partido"
                    params_tarjetas["numero_partido"] = numero_partido

            if estado_seleccionado:
                query_tarjetas += " AND pt.estado_pago = :estado_pago"
                query_inscripciones += " AND pi.estado_pago = :estado_pago"
                params_tarjetas["estado_pago"] = estado_seleccionado
                params_inscripciones["estado_pago"] = estado_seleccionado

            # Ejecutar consultas
            pagos_tarjetas = conn.execute(text(query_tarjetas), params_tarjetas).fetchall()

            # Solo buscar inscripciones si estamos filtrando por fecha
            if tipo_busqueda == 'fecha':
                pagos_inscripciones = conn.execute(text(query_inscripciones), params_inscripciones).fetchall()

    finally:
        conn.close()

    return render_template(
        'filtrar_pagos.html',
        pagos_tarjetas=pagos_tarjetas,
        pagos_inscripciones=pagos_inscripciones,
        fecha_seleccionada=fecha_seleccionada,
        numero_partido=numero_partido,
        estado_seleccionado=estado_seleccionado,
        equipos_existentes=equipos_existentes  # ✅ Corregido: ahora está definido
    )


if __name__ == '__main__':
    app.run(debug=True)


@app.route('/eliminar_registro', methods=['DELETE'])
def eliminar_registro():
    id = request.args.get('id')
    tipo = request.args.get('tipo')

    conn = get_db_connection()
    try:
        if tipo == 'tarjeta':
            query = "DELETE FROM pago_tarjetas WHERE id_pago = :id"
        elif tipo == 'inscripcion':
            query = "DELETE FROM pago_inscripcion WHERE id_inscripcion = :id"
        else:
            return jsonify({"success": False, "message": "Tipo de registro no válido"})

        conn.execute(text(query), {"id": id})
        conn.commit()
        return jsonify({"success": True, "message": "Registro eliminado correctamente"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})
    finally:
        conn.close()


@app.route('/editar_registro/<tipo>/<id>', methods=['GET'])
def editar_registro(tipo, id):
    conn = get_db_connection()
    try:
        if tipo == 'tarjeta':
            query = "SELECT * FROM pago_tarjetas WHERE id_pago = :id"
        elif tipo == 'inscripcion':
            query = "SELECT * FROM pago_inscripcion WHERE id_inscripcion = :id"
        else:
            return jsonify({"success": False, "message": "Tipo de registro no válido"})

        # 👇 CAMBIO IMPORTANTE
        result = conn.execute(text(query), {"id": id}).mappings().fetchone()

        if result:
            registro = dict(result)
            return jsonify({"success": True, "data": registro})
        else:
            return jsonify({"success": False, "message": "Registro no encontrado"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})
    finally:
        conn.close()


@app.route('/actualizar_registro/<tipo>/<id>', methods=['POST'])
def actualizar_registro(tipo, id):
    # Obtener los datos del formulario
    data = {key: value for key, value in request.form.items() if key != "valor_total_pagar"}  # Filtrar valor_total_pagar
    conn = get_db_connection()
    try:
        # Consulta para obtener el id_equipo basado en el nombre_equipo
        nombre_equipo = data.get("nombre_equipo")
        if nombre_equipo:
            equipo_query = "SELECT id_equipo FROM equipo_pagos WHERE nombre_equipo = :nombre_equipo"
            equipo_result = conn.execute(text(equipo_query), {"nombre_equipo": nombre_equipo}).fetchone()
            if equipo_result:
                data["id_equipo"] = equipo_result.id_equipo  # Agregar id_equipo a los datos
            else:
                return jsonify({"success": False, "message": "El nombre del equipo no existe en la base de datos."})

        if tipo == 'tarjeta':
            query = """
                UPDATE pago_tarjetas 
                SET nombre_equipo = :nombre_equipo, jugador = :jugador, categoria = :categoria, 
                    tarjetas_rojas = :tarjetas_rojas, tarjetas_amarillas = :tarjetas_amarillas, 
                    observaciones = :observaciones, metodo_pago = :metodo_pago, 
                    fecha_cobro = :fecha_cobro, estado_pago = :estado_pago, id_equipo = :id_equipo
                WHERE id_pago = :id
            """
        elif tipo == 'inscripcion':
            query = """
                UPDATE pago_inscripcion 
                SET nombre_equipo = :nombre_equipo, jugador = :jugador, categoria = :categoria, 
                    monto_a_cobrar = :monto_a_cobrar, observaciones = :observaciones, 
                    metodo_pago = :metodo_pago, fecha_inscripcion = :fecha_inscripcion, estado_pago = :estado_pago, id_equipo = :id_equipo
                WHERE id_inscripcion = :id
            """
        else:
            return jsonify({"success": False, "message": "Tipo de registro no válido"})

        # Ejecutar la consulta
        conn.execute(text(query), {**data, "id": id})
        conn.commit()
        return jsonify({"success": True, "message": "Registro actualizado correctamente"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})
    finally:
        conn.close()

@app.route('/reporte_semanal')
def reporte_semanal():
    # Obtener parámetros de la solicitud
    partido_seleccionado = request.args.get('partido', '1')  # Valor por defecto "Partido 1"
    timezone = pytz.timezone('UTC')

    # Calcular semana actual por defecto
    today_utc = datetime.now(timezone).date()
    start_of_week = today_utc - timedelta(days=today_utc.weekday())
    end_of_week = start_of_week + timedelta(days=6)

    # Si hay partido seleccionado, obtener fechas asociadas
    if partido_seleccionado != 'custom':
        conn = get_db_connection()
        try:
            result = conn.execute(text("""
                SELECT MIN(fecha_cobro) as inicio, MAX(fecha_cobro) as fin
                FROM pago_tarjetas 
                WHERE numero_partido_jugado = :partido
            """), {"partido": partido_seleccionado})

            fechas_partido = result.fetchone()
            if fechas_partido and fechas_partido.inicio:
                start_of_week = fechas_partido.inicio  # Ya es un objeto date
                end_of_week = fechas_partido.fin + timedelta(days=6)  # Ya es un objeto date
        finally:
            conn.close()

    # Consultar pagos de tarjetas e inscripciones
    conn = get_db_connection()
    try:
        # Tarjetas
        query_tarjetas = """

        SELECT pt.*, ep.nombre_equipo
                    FROM pago_tarjetas pt
                    LEFT JOIN equipo_pagos ep ON pt.id_equipo = ep.id_equipo
                    WHERE pt.numero_partido_jugado = :partido
                """
        result_tarjetas = conn.execute(text(query_tarjetas), {"partido": partido_seleccionado})
        tarjetas = result_tarjetas.fetchall()

        # Inscripciones
        query_inscripciones = """
            SELECT pi.*, ep.nombre_equipo
            FROM pago_inscripcion pi
            LEFT JOIN equipo_pagos ep ON pi.id_equipo = ep.id_equipo
            WHERE pi.fecha_inscripcion BETWEEN :start AND :end
        """
        result_inscripciones = conn.execute(text(query_inscripciones),
                                            {"start": start_of_week, "end": end_of_week})
        inscripciones = result_inscripciones.fetchall()

    finally:
        conn.close()

    # Calcular totales
    total_tarjetas_pendientes = sum(
        (t.tarjetas_rojas * 4 + t.tarjetas_amarillas * 2)
        for t in tarjetas if t.estado_pago == 'Pendiente'
    )
    total_inscripciones_pendientes = sum(
        i.monto_a_cobrar for i in inscripciones if i.estado_pago == 'Pendiente'
    )

    total_tarjetas_pagadas = sum(
        (t.tarjetas_rojas * 4 + t.tarjetas_amarillas * 2)
        for t in tarjetas if t.estado_pago == 'Pagado'
    )
    total_inscripciones_pagadas = sum(
        i.monto_a_cobrar for i in inscripciones if i.estado_pago == 'Pagado'
    )

    total_general_pendientes = total_tarjetas_pendientes + total_inscripciones_pendientes
    total_general_pagadas = total_tarjetas_pagadas + total_inscripciones_pagadas
    total_general = total_general_pendientes + total_general_pagadas

    # Agrupar pagos por día de la semana
    def get_nombre_dia(fecha):
        # Mapeo de números de días a nombres
        dias_semana = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
        return dias_semana[fecha.weekday()]

    pagos_por_dia = {}
    for pago in tarjetas + inscripciones:
        fecha = getattr(pago, 'fecha_cobro', None) or getattr(pago, 'fecha_inscripcion', None)
        if fecha:
            dia_nombre = get_nombre_dia(fecha)
            if dia_nombre not in pagos_por_dia:
                pagos_por_dia[dia_nombre] = {
                    'tarjetas': [],
                    'inscripciones': []
                }
            if hasattr(pago, 'tarjetas_rojas'):
                pagos_por_dia[dia_nombre]['tarjetas'].append(pago)
            else:
                pagos_por_dia[dia_nombre]['inscripciones'].append(pago)

    return render_template('reporte_semanal.html',
                           partido_seleccionado=partido_seleccionado,
                           start_of_week=start_of_week,
                           end_of_week=end_of_week,
                           pagos_por_dia=pagos_por_dia,
                           total_tarjetas_pendientes=total_tarjetas_pendientes,
                           total_inscripciones_pendientes=total_inscripciones_pendientes,
                           total_tarjetas_pagadas=total_tarjetas_pagadas,
                           total_inscripciones_pagadas=total_inscripciones_pagadas,
                           total_general_pendientes=total_general_pendientes,
                           total_general_pagadas=total_general_pagadas,
                           total_general=total_general
                           )