let map;
let directionsService;
let directionsRenderer;

async function initMap() {
    try {
        // Centrado en Santiago, Chile
        const santiago = { lat: -33.4489, lng: -70.6693 };
        
        // Inicializar el mapa
        map = new google.maps.Map(document.getElementById("map"), {
            zoom: 13,
            center: santiago,
        });

        // Inicializar servicios de direcciones
        directionsService = new google.maps.DirectionsService();
        directionsRenderer = new google.maps.DirectionsRenderer({
            map: map,
            panel: document.getElementById('route-info')
        });

        // Autocomplete para los inputs
        const originInput = document.getElementById("origin");
        const destinationInput = document.getElementById("destination");
        
        if (google.maps.places) {
            new google.maps.places.Autocomplete(originInput);
            new google.maps.places.Autocomplete(destinationInput);
        }

        // Agregar el event listener después de que todo esté inicializado
        document.getElementById('route-form').addEventListener('submit', handleRouteSubmit);

    } catch (error) {
        console.error('Error initializing map:', error);
        document.getElementById('map').innerHTML = 'Error loading map';
    }
}

async function handleRouteSubmit(e) {
    e.preventDefault();
    
    const origin = document.getElementById('origin').value;
    const destination = document.getElementById('destination').value;
    
    try {
        // Mostrar mensaje de carga
        document.getElementById('route-info').innerHTML = '<p>Calculando ruta...</p>';
        
        const response = await fetch(`/api/route?origin=${encodeURIComponent(origin)}&destination=${encodeURIComponent(destination)}`);
        const routeData = await response.json();
        
        if (response.ok && directionsService) {
            // Mostrar información de la ruta
            let routeHtml = `
                <h3>Información de la Ruta:</h3>
                <p>Desde: ${routeData.start_address}</p>
                <p>Hasta: ${routeData.end_address}</p>
                <p>Distancia: ${routeData.distance}</p>
                <p>Duración sin tráfico: ${routeData.duration}</p>
            `;

            if (routeData.duration_in_traffic) {
                routeHtml += `<p>Duración con tráfico: ${routeData.duration_in_traffic}</p>`;
                if (routeData.retraso_minutos > 0) {
                    routeHtml += `<p>Retraso por tráfico: ${routeData.retraso_minutos} minutos</p>`;
                }
            }

            document.getElementById('route-info').innerHTML = routeHtml;

            // Mostrar la ruta en el mapa
            const request = {
                origin: origin,
                destination: destination,
                travelMode: google.maps.TravelMode.DRIVING
            };

            await new Promise((resolve, reject) => {
                directionsService.route(request, (result, status) => {
                    if (status === 'OK') {
                        directionsRenderer.setDirections(result);
                        resolve();
                    } else {
                        reject(new Error(`Error al mostrar la ruta: ${status}`));
                    }
                });
            });
        } else {
            throw new Error(routeData.error || 'Error al calcular la ruta');
        }
    } catch (error) {
        console.error('Error:', error);
        document.getElementById('route-info').innerHTML = `
            <p class="error">Error: ${error.message}</p>
        `;
    }
}

// Asegurarse de que el script de Google Maps se cargue correctamente
window.initMap = initMap;