from flask import Flask, render_template, jsonify, request
import requests
import os
from dotenv import load_dotenv
import logging

load_dotenv()
app = Flask(__name__)
API_KEY = os.getenv('GOOGLE_MAPS_API_KEY')

# Configurar logging
logging.basicConfig(level=logging.DEBUG)

@app.route('/')
def index():
    return render_template('index.html', api_key=API_KEY)

@app.route('/api/route')
def get_route():
    origin = request.args.get('origin')
    destination = request.args.get('destination')
    
    url = (
        "https://maps.googleapis.com/maps/api/directions/json"
        f"?origin={origin}"
        f"&destination={destination}"
        f"&departure_time=now"
        f"&language=es"
        f"&key={API_KEY}"
    )
    
    try:
        app.logger.debug(f"Consultando URL: {url}")
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        if data['status'] == 'OK' and data['routes']:
            leg = data['routes'][0]['legs'][0]
            
            # Calcular retraso si hay información de tráfico
            duration_ideal_seconds = leg['duration']['value']
            duration_real_seconds = leg.get('duration_in_traffic', {}).get('value', duration_ideal_seconds)
            retraso_minutos = round((duration_real_seconds - duration_ideal_seconds) / 60)
            
            route_info = {
                'start_address': leg['start_address'],
                'end_address': leg['end_address'],
                'distance': leg['distance']['text'],
                'duration': leg['duration']['text'],
                'duration_in_traffic': leg.get('duration_in_traffic', {}).get('text'),
                'retraso_minutos': retraso_minutos if retraso_minutos > 0 else 0,
                'polyline': data['routes'][0]['overview_polyline']['points']
            }
            
            app.logger.debug(f"Ruta calculada exitosamente: {route_info}")
            return jsonify(route_info)
        else:
            error_msg = f"Error en la respuesta de la API: {data.get('status')}"
            app.logger.error(error_msg)
            return jsonify({'error': error_msg}), 400
            
    except requests.exceptions.RequestException as e:
        error_msg = f"Error de conexión: {str(e)}"
        app.logger.error(error_msg)
        return jsonify({'error': error_msg}), 500

if __name__ == '__main__':
    app.run(debug=True)