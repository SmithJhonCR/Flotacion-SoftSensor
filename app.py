import os
import time
import threading
from flask import Flask, render_template, jsonify

app = Flask(__name__, template_folder='.')
AREA_CELDA = 0.09 
ALTURA_MAX = 45.0 
Q_ALIMENTACION = 15.0 

niveles = [30.0, 30.0, 30.0]     
setpoints = [30.0, 30.0, 30.0]   
Q_tailings = [10.0, 10.0, 10.0]  
DT = 0.5 

def bucle_control():
    global niveles, Q_tailings
    
    while True:
        for i in range(3):
            # Flujo de entrada en serie
            if i == 0:
                Q_in = Q_ALIMENTACION
            else:
                Q_in = Q_tailings[i-1] 

            error = setpoints[i] - niveles[i]
            
            # --- CORRECCIÓN AQUÍ ---
            # Ganancia suave y límite estricto de bombeo
            Kc = 0.1   # Muy baja para que no reaccione de golpe
            Ti = 20.0 
            
            Q_out_pid = (Kc * error) + (Kc / Ti) * (error * DT) 
            
            # La bomba solo puede bombear entre 0 y 12 LPM (así no se vacía de golpe)
            Q_tailings[i] = max(0.0, min(12.0, Q_out_pid + 10.0)) 
            
            # Modelo Matemático (Balance de masa)
            delta_H = ((Q_in - Q_tailings[i]) / 60000.0) / AREA_CELDA * 100.0 * DT
            
            niveles[i] += delta_H
            niveles[i] = max(0.0, min(ALTURA_MAX, niveles[i]))
            
        time.sleep(DT)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/datos')
def obtener_datos():
    return jsonify({
        'niveles': niveles,
        'setpoints': setpoints,
        'flujos': Q_tailings
    })

@app.route('/api/setpoint/<int:celda>/<float:valor>')
def cambiar_setpoint(celda, valor):
    if 0 <= celda < 3:
        setpoints[celda] = valor
    return jsonify({"status": "ok"})

if __name__ == '__main__':
    hilo = threading.Thread(target=bucle_control, daemon=True)
    hilo.start()
    puerto = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=puerto)