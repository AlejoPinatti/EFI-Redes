from flask import Flask, Response, render_template, request
from flask_socketio import SocketIO, emit
import cv2
import numpy as np
import base64
import threading
import time

# --- Variables Globales ---
# ¡YA NO NECESITAMOS global_frame!
# El servidor ahora es solo un "pasamanos" (forwarder)

control_state = {
    "torch_on": False,
    "device_info": None,
    "stream_on": False,
    "last_frame_time": 0,
    "cycle_camera_request": 0
}
control_lock = threading.Lock()

app = Flask(__name__)
app.config['SECRET_KEY'] = 'tu_clave_secreta_aqui!'
socketio = SocketIO(app)

# --- (Rutas / y /phone sin cambios) ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/phone')
def phone_client():
    return render_template('phone.html')

# --- (Ruta /upload ELIMINADA) ---

# --- (Ruta /stream.mjpeg ELIMINADA) ---

# --- NUEVOS EVENTOS DE WEBSOCKET ---
@socketio.on('connect')
def handle_connect():
    print('Cliente conectado')

@socketio.on('disconnect')
def handle_disconnect():
    print('Cliente desconectado')

@socketio.on('send_frame')
def handle_frame(data_url):
    """
    Recibe un frame de la cámara y lo retransmite
    a todos los visores conectados.
    """
    # 1. Actualizar el "latido" para el estado "EN VIVO"
    with control_lock:
        control_state["last_frame_time"] = time.time()
    
    # 2. Retransmitir el frame a todos (broadcast=True)
    #    menos al que lo envió (include_self=False)
    emit('new_frame', data_url, broadcast=True, include_self=False)

# --- (RUTAS DE CONTROL HTTP - SIN CAMBIOS) ---
@app.route('/control/command', methods=['POST'])
def control_command():
    global control_state, control_lock
    data = request.get_json()
    with control_lock:
        if 'torch' in data:
            control_state['torch_on'] = (data['torch'] == 'on')
        if 'stream' in data:
            control_state['stream_on'] = (data['stream'] == 'on')
        if 'cycle_camera' in data and data['cycle_camera'] == 'next':
            control_state['cycle_camera_request'] += 1
    return "Comando recibido", 200

@app.route('/device/info', methods=['POST'])
def device_info():
    global control_state, control_lock
    info = request.get_json()
    with control_lock:
        control_state['device_info'] = info
    return "Info OK", 200

@app.route('/control/poll', methods=['GET'])
def control_poll():
    global control_state, control_lock
    with control_lock:
        return control_state 

# --- (Ejecución del Servidor - MODIFICADO) ---
if __name__ == '__main__':
    print("Iniciando servidor WebSocket en http://0.0.0.0:8000")
    # Usamos socketio.run() en lugar de app.run()
    socketio.run(app, host='0.0.0.0', port=8000, allow_unsafe_werkzeug=True)