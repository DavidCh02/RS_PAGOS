from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# Initialize SQLAlchemy instance
db = SQLAlchemy()

class Inscripcion(db.Model):
    __tablename__ = 'inscripcion'
    id = db.Column(db.Integer, primary_key=True)
    equipo_id = db.Column(db.Integer, db.ForeignKey('equipo_pagos.id_equipo'))
    fecha_inscripcion = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    categoria = db.Column(db.String(50))
    tipo_deporte = db.Column(db.String(50))
    subcategoria = db.Column(db.String(50))
    nombre_dirigente = db.Column(db.String(100))
    telefono_dirigente = db.Column(db.String(20))
    email_dirigente = db.Column(db.String(100))
    comprobante_pago = db.Column(db.String(255))
    estado_verificacion = db.Column(db.String(20), default='Pendiente')
    total_jugadores = db.Column(db.Integer)
    monto_base = db.Column(db.Float, default=100.0)
    monto_extra = db.Column(db.Float, default=0.0)
    monto_total = db.Column(db.Float)
    observaciones = db.Column(db.Text)

class JugadorInscrito(db.Model):
    __tablename__ = 'jugador_inscrito'
    id = db.Column(db.Integer, primary_key=True)
    inscripcion_id = db.Column(db.Integer, db.ForeignKey('inscripcion.id'))
    nombre = db.Column(db.String(100))
    cedula = db.Column(db.String(20))
    fecha_nacimiento = db.Column(db.Date)
    posicion = db.Column(db.String(50))
    numero_camiseta = db.Column(db.Integer)
    es_dirigente = db.Column(db.Boolean, default=False)
    telefono = db.Column(db.String(20))
    email = db.Column(db.String(100))