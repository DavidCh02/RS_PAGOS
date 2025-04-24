# inscripciones.py
import json

from flask import Blueprint, request, jsonify, render_template
from werkzeug.utils import secure_filename
from datetime import datetime
import os
from sqlalchemy import text
from database import get_db_connection  # Importa desde database.py

# Crea el Blueprint
inscripciones_bp = Blueprint('inscripcion', __name__)

# Configuración de carga de archivos
UPLOAD_FOLDER = 'static/img/comprobantes'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf'}


def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@inscripciones_bp.route('/inscripcion/guardar', methods=['POST'])
def guardar_inscripcion():
    conn = get_db_connection()
    try:
        # Add debug print
        print("Form data received:", request.form)
        
        # Lógica para procesar la inscripción
        data = {
            'categoria': request.form.get('categoria'),
            'tipo_deporte': request.form.get('deporte'),
            'subcategoria': request.form.get('subcategoria'),
            'nombre_equipo': request.form.get('nombreEquipo'),
            'nombre_dirigente': request.form.get('nombreDirigente'),
            'telefono_dirigente': request.form.get('telefonoDirigente'),
            'email_dirigente': request.form.get('emailDirigente'),
            'total_jugadores': request.form.get('total_jugadores', type=int),
            'monto_base': request.form.get('monto_base', type=float),
            'monto_extra': request.form.get('monto_extra', type=float),
            'monto_total': request.form.get('monto_total', type=float),
            'jugadores': request.form.get('jugadores')
        }
        
        # Add debug print
        print("Processed data:", data)
        
        # Manejo del comprobante de pago
        file = request.files.get('comprobantePago')
        if file and allowed_file(file.filename):
            filename = secure_filename(f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}")
            file.save(os.path.join(UPLOAD_FOLDER, filename))
            data['comprobante_pago'] = filename
        else:
            return jsonify({'success': False, 'message': 'Archivo no válido'}), 400

        # Insertar en la tabla inscripcion
        inscripcion_query = """
            INSERT INTO inscripcion (
                equipo_id, fecha_inscripcion, categoria, tipo_deporte, subcategoria,
                nombre_equipo, nombre_dirigente, telefono_dirigente, email_dirigente,
                comprobante_pago, estado, total_jugadores,
                monto_base, monto_extra, monto_total
            ) VALUES (
                NULL, CURRENT_TIMESTAMP, :categoria, :tipo_deporte, :subcategoria,
                :nombre_equipo, :nombre_dirigente, :telefono_dirigente, :email_dirigente,
                :comprobante_pago, 'pendiente', :total_jugadores,
                :monto_base, :monto_extra, :monto_total
            ) RETURNING id
        """
        result = conn.execute(text(inscripcion_query), data)
        inscripcion_id = result.fetchone()[0]

        # Insertar jugadores
        jugadores = json.loads(data['jugadores'])
        for jugador in jugadores:
            jugador_data = {
                'inscripcion_id': inscripcion_id,
                'nombre': jugador['nombre'],
                'cedula': jugador['cedula'],
                'numero_camiseta': jugador['numero_camiseta'],
                'es_dirigente': request.form.get('dirigenteJugador') == 'true'
            }

            jugador_query = """
                INSERT INTO jugador_inscrito (
                    inscripcion_id, nombre, cedula, numero_camiseta, es_dirigente
                ) VALUES (
                    :inscripcion_id, :nombre, :cedula, :numero_camiseta, :es_dirigente
                )
            """
            conn.execute(text(jugador_query), jugador_data)

        conn.commit()
        return jsonify({'success': True, 'message': 'Inscripción guardada', 'id': inscripcion_id})

    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

    finally:
        conn.close()


@inscripciones_bp.route('/admin/inscripciones')
def admin_inscripciones():
    return render_template('admin_inscripcion.html')

@inscripciones_bp.route('/admin/inscripciones/lista')
def lista_inscripciones():
    conn = get_db_connection()
    try:
        query = """
            SELECT 
                id, 
                fecha_inscripcion, 
                nombre_equipo, 
                categoria, 
                tipo_deporte, 
                COALESCE(estado, 'pendiente') as estado
            FROM inscripcion
            ORDER BY fecha_inscripcion DESC
        """
        result = conn.execute(text(query))
        
        inscripciones = []
        for row in result:
            inscripcion = {
                'id': row.id,
                'fecha_inscripcion': row.fecha_inscripcion.isoformat() if row.fecha_inscripcion else None,
                'nombre_equipo': row.nombre_equipo,
                'categoria': row.categoria,
                'tipo_deporte': row.tipo_deporte,
                'estado': row.estado or 'pendiente'
            }
            inscripciones.append(inscripcion)
        
        return jsonify({'inscripciones': inscripciones})
    except Exception as e:
        print(f"Error in lista_inscripciones: {str(e)}")
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@inscripciones_bp.route('/admin/inscripciones/<int:id>')
def detalle_inscripcion(id):
    conn = get_db_connection()
    try:
        # Get inscription details
        query = """
            SELECT 
                id,
                fecha_inscripcion,
                nombre_equipo,
                categoria,
                tipo_deporte,
                subcategoria,
                nombre_dirigente,
                telefono_dirigente,
                email_dirigente,
                comprobante_pago,
                estado,
                total_jugadores,
                monto_base,
                monto_extra,
                monto_total
            FROM inscripcion
            WHERE id = :id
        """
        result = conn.execute(text(query), {'id': id}).fetchone()
        
        if not result:
            return jsonify({'error': 'Inscripción no encontrada'}), 404
        
        # Convert row to dictionary explicitly
        inscripcion = {
            'id': result.id,
            'fecha_inscripcion': result.fecha_inscripcion.isoformat() if result.fecha_inscripcion else None,
            'nombre_equipo': result.nombre_equipo,
            'categoria': result.categoria,
            'tipo_deporte': result.tipo_deporte,
            'subcategoria': result.subcategoria,
            'nombre_dirigente': result.nombre_dirigente,
            'telefono_dirigente': result.telefono_dirigente,
            'email_dirigente': result.email_dirigente,
            'comprobante_pago': result.comprobante_pago,
            'estado': result.estado,
            'total_jugadores': result.total_jugadores,
            'monto_base': result.monto_base,
            'monto_extra': result.monto_extra,
            'monto_total': result.monto_total
        }
        
        # Get players for this inscription
        query_players = """
            SELECT nombre, cedula, numero_camiseta
            FROM jugador_inscrito
            WHERE inscripcion_id = :id
        """
        jugadores = conn.execute(text(query_players), {'id': id}).fetchall()
        
        # Convert players to list of dictionaries
        inscripcion['jugadores'] = [
            {
                'nombre': jugador.nombre,
                'cedula': jugador.cedula,
                'numero_camiseta': jugador.numero_camiseta
            }
            for jugador in jugadores
        ]
        
        return jsonify(inscripcion)
    except Exception as e:
        print(f"Error in detalle_inscripcion: {str(e)}")
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@inscripciones_bp.route('/admin/inscripciones/<int:id>/status', methods=['POST'])
def actualizar_estado(id):
    conn = get_db_connection()
    try:
        data = request.get_json()
        status = data.get('status')
        
        if status not in ['aprobado', 'rechazado', 'pendiente']:
            return jsonify({'error': 'Estado inválido'}), 400
        
        query = """
            UPDATE inscripcion
            SET estado = :status
            WHERE id = :id
        """
        conn.execute(text(query), {'status': status, 'id': id})
        conn.commit()
        
        return jsonify({'success': True})
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()