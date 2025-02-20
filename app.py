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
                numero_partido_jugado = int(request.form['numero_partido_jugado'])
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
    estado_seleccionado = None
    pagos_tarjetas = []
    pagos_inscripciones = []
    conn = get_db_connection()
    try:
        if request.method == 'POST':
            # Obtener la fecha y el estado seleccionados
            fecha_seleccionada = request.form.get('fecha_cliente')
            estado_seleccionado = request.form.get('estado_pago')

            # Consultar pagos de tarjetas según los filtros
            query_tarjetas = """
            SELECT pt.*, ep.nombre_equipo
            FROM pago_tarjetas pt
            LEFT JOIN equipo_pagos ep ON pt.id_equipo = ep.id_equipo
            WHERE 1=1
            """
            params_tarjetas = {}
            if fecha_seleccionada:
                query_tarjetas += " AND pt.fecha_cobro = :fecha"
                params_tarjetas["fecha"] = fecha_seleccionada
            if estado_seleccionado:
                query_tarjetas += " AND pt.estado_pago = :estado_pago"
                params_tarjetas["estado_pago"] = estado_seleccionado

            result_tarjetas = conn.execute(text(query_tarjetas), params_tarjetas)
            pagos_tarjetas = result_tarjetas.fetchall()

            # Consultar pagos de inscripción según los filtros
            query_inscripciones = """
            SELECT pi.*, ep.nombre_equipo
            FROM pago_inscripcion pi
            LEFT JOIN equipo_pagos ep ON pi.id_equipo = ep.id_equipo
            WHERE 1=1
            """
            params_inscripciones = {}
            if fecha_seleccionada:
                query_inscripciones += " AND pi.fecha_inscripcion = :fecha"
                params_inscripciones["fecha"] = fecha_seleccionada
            if estado_seleccionado:
                query_inscripciones += " AND pi.estado_pago = :estado_pago"
                params_inscripciones["estado_pago"] = estado_seleccionado

            result_inscripciones = conn.execute(text(query_inscripciones), params_inscripciones)
            pagos_inscripciones = result_inscripciones.fetchall()

    finally:
        conn.close()

    return render_template(
        'filtrar_pagos.html',
        pagos_tarjetas=pagos_tarjetas,
        pagos_inscripciones=pagos_inscripciones,
        fecha_seleccionada=fecha_seleccionada,
        estado_seleccionado=estado_seleccionado
    )
if __name__ == '__main__':
    app.run(debug=True)





@app.route('/eliminar_registro', methods=['DELETE'])
def eliminar_registro():
    id_registro = request.args.get('id')
    tipo = request.args.get('tipo')  # "tarjeta" o "inscripcion"
    conn = get_db_connection()
    try:
        if tipo == "tarjeta":
            conn.execute(text("DELETE FROM pago_tarjetas WHERE id_pago = :id_registro"), {"id_registro": id_registro})
        elif tipo == "inscripcion":
            conn.execute(text("DELETE FROM pago_inscripcion WHERE id_inscripcion = :id_registro"), {"id_registro": id_registro})
        conn.commit()  # Confirmar los cambios
        return jsonify({"success": True, "message": "Registro eliminado correctamente."})
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "message": str(e)})
    finally:
        conn.close()
@app.route('/editar_registro_tarjeta', methods=['POST'])
def editar_registro_tarjeta():
    id_pago = request.form.get('id_pago_tarjeta')
    jugador = request.form.get('jugador_editar_tarjeta')
    categoria = request.form.get('categoria_editar_tarjeta')
    tarjetas_rojas = request.form.get('tarjetas_rojas_editar')
    tarjetas_amarillas = request.form.get('tarjetas_amarillas_editar')
    observaciones = request.form.get('observaciones_editar_tarjeta')
    metodo_pago = request.form.get('metodo_pago_editar_tarjeta')
    fecha_pago = request.form.get('fecha_pago_editar_tarjeta')
    estado_pago = request.form.get('estado_pago_editar_tarjeta')

    # Validar que los campos obligatorios no estén vacíos
    if not all([id_pago, jugador, categoria, fecha_pago, estado_pago]):
        flash("Todos los campos obligatorios deben estar completos.", "error")
        return redirect(url_for('filtrar_pagos'))

    conn = get_db_connection()
    try:
        conn.execute(text("""
        UPDATE pago_tarjetas
        SET jugador = :jugador, categoria = :categoria, tarjetas_rojas = :tarjetas_rojas,
            tarjetas_amarillas = :tarjetas_amarillas, observaciones = :observaciones,
            metodo_pago = :metodo_pago, fecha_cobro = :fecha_pago, estado_pago = :estado_pago
        WHERE id_pago = :id_pago
        """), {
            "id_pago": id_pago,
            "jugador": jugador,
            "categoria": categoria,
            "tarjetas_rojas": tarjetas_rojas or 0,  # Valor predeterminado si está vacío
            "tarjetas_amarillas": tarjetas_amarillas or 0,  # Valor predeterminado si está vacío
            "observaciones": observaciones,
            "metodo_pago": metodo_pago,
            "fecha_pago": fecha_pago,
            "estado_pago": estado_pago
        })
        conn.commit()  # Confirmar los cambios
        flash("Registro actualizado correctamente.", "success")  # Mensaje de éxito
        return redirect(url_for('filtrar_pagos'))  # Redirigir a la página de edición
    except Exception as e:
        conn.rollback()
        print(f"Error detallado: {str(e)}")  # Imprime el error en la terminal
        flash(f"Error al actualizar el registro: {str(e)}", "error")  # Mensaje de error
        return redirect(url_for('filtrar_pagos'))  # Redirigir a la página de edición
    finally:
        conn.close()

@app.route('/editar_registro_inscripcion', methods=['POST'])
def editar_registro_inscripcion():
    # Obtener los datos del formulario
    id_registro = request.form.get('id_registro')
    jugador = request.form.get('jugador_editar')
    categoria = request.form.get('categoria_editar')
    fecha = request.form.get('fecha_editar')
    estado = request.form.get('estado_editar')
    monto = request.form.get('monto_editar')  # Añadido para manejar el monto
    metodo_pago = request.form.get('metodo_pago_editar')  # Añadido para manejar el método de pago
    observaciones = request.form.get('observaciones_editar')  # Añadido para manejar observaciones
    id_equipo = request.form.get('equipo_editar')  # Añadido para manejar el ID del equipo

    # Validar que los campos obligatorios no estén vacíos
    if not all([id_registro, jugador, categoria, fecha, estado]):
        return jsonify({"success": False, "message": "Todos los campos obligatorios deben estar completos."})

    # Conectar a la base de datos
    conn = get_db_connection()
    try:
        # Actualizar el registro en la tabla `pago_inscripcion`
        conn.execute(text("""
            UPDATE pago_inscripcion
            SET jugador = :jugador, categoria = :categoria, fecha_inscripcion = :fecha,
                estado_pago = :estado, monto_a_cobrar = :monto, metodo_pago = :metodo_pago,
                observaciones = :observaciones, id_equipo = :id_equipo
            WHERE id_inscripcion = :id_registro
        """), {
            "jugador": jugador,
            "categoria": categoria,
            "fecha": fecha,
            "estado": estado,
            "monto": float(monto) if monto else 0,  # Convertir a float o establecer como 0 si está vacío
            "metodo_pago": metodo_pago,
            "observaciones": observaciones,
            "id_equipo": int(id_equipo) if id_equipo else None,  # Si no se selecciona un equipo, establecer como NULL
            "id_registro": id_registro
        })
        conn.commit()  # Confirmar los cambios
        return jsonify({"success": True, "message": "Registro actualizado correctamente."})
    except Exception as e:
        conn.rollback()
        print(f"Error detallado: {str(e)}")  # Imprime el error en la terminal
        return jsonify({"success": False, "message": f"Error al actualizar el registro: {str(e)}"})
    finally:
        conn.close()

@app.route('/editar_registro', methods=['POST'])
def editar_registro():
    id_registro = request.form.get('id_registro')
    jugador = request.form.get('jugador_editar')
    categoria = request.form.get('categoria_editar')
    fecha = request.form.get('fecha_editar')
    estado = request.form.get('estado_editar')
    monto = request.form.get('monto_editar')  # Añadido para manejar el monto
    metodo_pago = request.form.get('metodo_pago_editar')  # Añadido para manejar el método de pago
    observaciones = request.form.get('observaciones_editar')  # Añadido para manejar observaciones
    id_equipo = request.form.get('equipo_editar')  # Añadido para manejar el ID del equipo

    conn = get_db_connection()
    try:
        conn.execute(text("""
        UPDATE pago_inscripcion
        SET jugador = :jugador, categoria = :categoria, fecha_inscripcion = :fecha,
            estado_pago = :estado, monto_a_cobrar = :monto, metodo_pago = :metodo_pago,
            observaciones = :observaciones, id_equipo = :id_equipo
        WHERE id_inscripcion = :id_registro
        """), {
            "jugador": jugador,
            "categoria": categoria,
            "fecha": fecha,
            "estado": estado,
            "monto": monto,
            "metodo_pago": metodo_pago,
            "observaciones": observaciones,
            "id_equipo": id_equipo or None,  # Si no se selecciona un equipo, establecer como NULL
            "id_registro": id_registro
        })
        conn.commit()  # Confirmar los cambios
        return jsonify({"success": True, "message": "Registro actualizado correctamente."})
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "message": str(e)})
    finally:
        conn.close()