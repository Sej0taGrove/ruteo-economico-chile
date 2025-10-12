import requests
import json

# --- ADVERTENCIA DE SEGURIDAD ---
# Reemplaza el texto de abajo con tu NUEVA y SEGURA clave de API.
# Mantenla siempre en privado.

API_KEY = "AIzaSyDGZkrGCQT3rtvAEqX-lVl8exmNt881af4 "

# Puntos de la ruta especificada
# Es buena práctica ser lo más específico posible con la dirección.
origen = "Av. Vicuña Mackenna 4927, San Joaquín, Santiago, Chile"
destino = "Universidad Diego Portales, Santiago, Chile"

# Construcción de la URL de la API
# El parámetro 'departure_time=now' es OBLIGATORIO para obtener datos de tráfico.
url = (
    "https://maps.googleapis.com/maps/api/directions/json"
    f"?origin={origen}"
    f"&destination={destino}"
    f"&departure_time=now"  # <--- ¡Obligatorio para el tráfico!
    f"&language=es"  # <--- Pedimos la respuesta en español
    f"&key={API_KEY}"
)

print(f"Consultando la ruta desde '{origen}' hasta '{destino}'...")

try:
    # Hacemos la petición a la API de Google
    response = requests.get(url)
    response.raise_for_status()  # Lanza un error si la petición HTTP falla (ej. error 404, 500)

    # Convertimos la respuesta de texto a un diccionario de Python
    data = response.json()

    # Verificamos que la API haya encontrado una ruta exitosamente
    if data['status'] == 'OK' and data['routes']:
        # Extraemos la información de la primera ruta sugerida
        leg = data['routes'][0]['legs'][0]

        start_address = leg['start_address']
        end_address = leg['end_address']
        distance = leg['distance']['text']

        # Obtenemos las dos duraciones clave
        duration_ideal_text = leg['duration']['text']
        duration_real_text = leg.get('duration_in_traffic', {}).get('text')

        # También obtenemos los valores en segundos para poder calcular la diferencia
        duration_ideal_seconds = leg['duration']['value']
        duration_real_seconds = leg.get('duration_in_traffic', {}).get('value', duration_ideal_seconds)

        print("\n--- RESULTADO DEL CÁLCULO DE RUTA ---")
        print(f"Desde: {start_address}")
        print(f"Hasta: {end_address}")
        print(f"Distancia: {distance}")
        print("---------------------------------------")
        print(f"Duración sin tráfico (ideal): {duration_ideal_text}")

        if duration_real_text:
            print(f"Duración con tráfico actual: {duration_real_text}")

            # Calculamos el impacto de la congestión
            retraso_segundos = duration_real_seconds - duration_ideal_seconds
            retraso_minutos = round(retraso_segundos / 60)

            print("\nANÁLISIS DE LA AMENAZA (CONGESTIÓN):")
            if retraso_minutos > 1:
                print(f"El tráfico actual está agregando aproximadamente {retraso_minutos} minutos a este viaje.")
                print("Esta es la 'evidencia' numérica y geolocalizada de la amenaza.")
            else:
                print("El tráfico en esta ruta es fluido en este momento.")

        else:
            print("No se encontró información de tráfico en tiempo real para esta ruta.")

    else:
        print(f"Error en la respuesta de la API: {data.get('status')}")
        if data.get('error_message'):
            print(f"Mensaje de error: {data['error_message']}")

except requests.exceptions.RequestException as e:
    print(f"Error de conexión al intentar llamar a la API: {e}")