#------------------------------IMPORT------------------------------#
from flask import Flask, request 
from flask.json import jsonify
from flask_sqlalchemy import SQLAlchemy
import jwt
import bcrypt
from datetime import datetime
#------------------------------------------------------------------#




#-------------------------------INIT-------------------------------#
#--------------ENV--------------#
env = open('.env', 'r')
env = ast.literal_eval(env.read())
#-------------------------------#


#-------------FLASK-------------#
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = env['DATABASE_URI']
app.config['SECRET_KEY'] = env['SESSION_SECRET']
#-------------------------------#


#----------SQL-ALCHEMY----------#
db = SQLAlchemy(app)
#-------------------------------#
#------------------------------------------------------------------#




#-----------------------------MODELOS------------------------------#
#------------USUARIO------------#
class Usuario(db.Model):
	__tablename__ = 'usuarios'
	id = db.Column(db.Integer, primary_key=True)
	nombre = db.Column(db.String(100), unique=True, nullable=False)
	password = db.Column(db.String(100), nullable=False)
	def __init__(self, nombre, password):
		self.nombre = nombre
		self.password = password
#-------------------------------#


#------------MENSAJE------------#
class Mensaje(db.Model):
	__tablename__ = 'mensajes'
	id = db.Column(db.Integer, primary_key=True)
	usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
	contenido = db.Column(db.String(100))
	timestamp = db.Column(db.DateTime)
   
	def __init__(self, usuario_id, contenido):
		self.usuario_id = usuario_id
		self.contenido = contenido
		self.timestamp = datetime.utcnow()
#-------------------------------#
#----------------------------------------------------------------#





#------------------------------RUTAS-----------------------------#
#------------DEFAULT------------#
@app.route('/')
def index():
    return 'Hello world'
#-------------------------------#


#------------USUARIO------------#
@app.route('/usuario', methods=['POST', 'GET'])
def usuario():
	if request.method == 'POST':
		crypted_pass = bcrypt.hashpw(request.form.get('password').encode('utf-8'), bcrypt.gensalt())
		usuario = Usuario(request.form.get('nombre'), crypted_pass)
		db.session.add(usuario)
		db.session.commit()
		return '', 200
	else:
		usuarios = Usuario.query.all()
		data = {}
		for usuario in usuarios:
			data[usuario.id] = usuario.nombre
		return jsonify(data), {'Content-Type': 'application/json'}

@app.route('/usuario/<nombre>')
def usuario_nombre(nombre):
	usuario = Usuario.query.filter_by(nombre=nombre).first();
	if usuario:
		return jsonify({'id':usuario.id}), {'Content-Type': 'application/json'}
	else:
		return ''

@app.route('/usuario/<id_usuario>/<password>')
def usuario_validacion(id_usuario, password):
	usuario = Usuario.query.filter_by(id=id_usuario).first();
	if bcrypt.checkpw(password.encode('utf-8'), usuario.password):
		token = jwt.encode({'id': id_usuario}, env['JWT_SECRET'], algorithm='HS256')
		return jsonify({'token':token.decode('utf-8')}), {'Content-Type': 'application/json'}
	return 403
#-------------------------------#


#------------MENSAJES-----------#
@app.route('/mensajes', methods=['POST', 'GET'])
def mensajes():
	token = request.headers.get('Authorization')
	bytes_token = token.encode('utf-8')
	usuario_id = jwt.decode(token, env['JWT_SECRET'], algorithms=['HS256']).get('id')
	
	if request.method == 'POST':
		mensaje = Mensaje(usuario_id, request.form.get('contenido'))
		db.session.add(mensaje)
		db.session.commit()
		return '', 200
	else:
		mensajes = Mensaje.query.filter_by(usuario_id=usuario_id).all();
		data = {}
		for mensaje in mensajes:
			data[mensaje.id] = {'timestamp':mensaje.timestamp, 'contenido':mensaje.contenido}
		return jsonify(data), {'Content-Type': 'application/json'}
#-------------------------------#
#----------------------------------------------------------------#





#------------------------------MAIN------------------------------#
if __name__ == '__main__':
	db.create_all()
	app.run(host=env['CLIENT_HOST'], port=env['CLIENT_PORT'])
#----------------------------------------------------------------#
