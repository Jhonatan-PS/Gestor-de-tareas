from flask import Flask
from App import db
import datetime

class Tareas(db.Model):
    id = db.Column(db.Integer,Primary_key=True)
    Nombre = db.Column(db.String(50), nullable=False)
    Fecha_Inicio = db.Column(db.DateTime,default=datetime.utcnow)
    Fecha_Fin = db.Column(db.DateTime)
    Estado = db.Column(db.String(20),default='Por asignar')