#------------------------------IMPORT------------------------------#
from flask import Flask, render_template, request, url_for, redirect, session
import requests
import queue
import json
import ast
from requests.exceptions import ConnectionError
#------------------------------------------------------------------#




#-------------------------------INIT-------------------------------#
#--------------ENV--------------#
env = open('.env', 'r')
env = ast.literal_eval(env.read())
#-------------------------------#


#-------------FLASK-------------#
app = Flask(__name__)
app.secret_key = env['SESSION_SECRET']
#-------------------------------#


#--------------MAP--------------#
mapa_cola = {}
semaforo = {}
#-------------------------------#
#------------------------------------------------------------------#


#------------------------------RUTAS-----------------------------#
#------------DEFAULT------------#
@app.route('/')
def index():
	return render_template('index.html')
#-------------------------------#


#------------MENSAJE------------#
@app.route('/mensajes', methods=['POST', 'GET'])
def mensajes():

	headers = {"Authorization":session['token']}
	if request.method == 'POST':
		try:
			if not (session['token'] in semaforo):
				semaforo[session['token']] = True
			payload = {'contenido':request.form['contenido']}
			url = env['SERVER_HOST']+':'+env['SERVER_PORT']+'/mensajes'
			if not (session['token'] in mapa_cola):
				mapa_cola[session['token']] = queue.Queue()
			mapa_cola[session['token']].put(payload)
			if semaforo[session['token']]:
				return redirect(url_for('mensajes'))
			else:
				semaforo[session['token']] = True
			while not mapa_cola[session['token']].empty():	
				requests.post(url, data=list(mapa_cola[session['token']].queue)[0], headers=headers)
				mapa_cola[session['token']].get()
			semaforo[session['token']] = False
			return redirect(url_for('mensajes'))
		except ConnectionError:
			return redirect(url_for('mensajes'))
	else:
		error = ""
		mensajes={}
		try:
			url = env['SERVER_HOST']+':'+env['SERVER_PORT']+'/mensajes'
			response = requests.get(url, headers=headers)
			mensajes = response.json()
		except ConnectionError:
			error = "Error de conexion"
		return render_template('mensajes.html', error = error, mensajes = mensajes)
#-------------------------------#


#-------------LOGIN-------------#
@app.route('/login', methods=['POST', 'GET'])
def login():

	if request.method == 'POST':
		try: 
			url = env['SERVER_HOST']+':'+env['SERVER_PORT']+'/usuario/'+request.form['nombre']
			response = requests.get(url)
			usuario_id = str(response.json()['id'])
			url = env['SERVER_HOST']+':'+env['SERVER_PORT']+'/usuario/'+usuario_id+'/'+request.form['password']
			response = requests.get(url)
			session.clear()
			session['nombre'] = request.form['nombre']
			session['token'] = response.json()['token']
			return redirect(url_for('index'))
		except ConnectionError:
			redirect(url_for('login'))
	else:
		return render_template('login.html')
#-------------------------------#


#-----------REGISTRAR-----------#
@app.route('/registrar', methods=['POST', 'GET'])
def registrar():

	if request.method == 'POST':
		try:
			payload = {'nombre':request.form['nombre'], 'password':request.form['password']}
			url = env['SERVER_HOST']+':'+env['SERVER_PORT']+'/usuario'
			requests.post(url, data=payload)
			return redirect(url_for('login'))
		except ConnectionError:
			redirect(url_for('registrar'))
	else:
		return render_template('registrar.html')
#-------------------------------#


#------------LOGOUT-------------#
@app.route('/logout')
def logout():
	session.clear()
	return redirect(url_for('index'))
#-------------------------------#


#------------------------------MAIN------------------------------#
if __name__ == '__main__':
	app.run(host=env['CLIENT_HOST'], port=env['CLIENT_PORT'])
#----------------------------------------------------------------#
