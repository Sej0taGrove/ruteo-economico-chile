(() => {
    let map;
    let routeLayer;
    let markers = [];

    function initMap() {
        // Inicializar mapa centrado en Chile
        map = L.map('map').setView([-33.4489, -70.6693], 13);
        
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors'
        }).addTo(map);

        routeLayer = L.layerGroup().addTo(map);

        // Manejar clics en el mapa
        map.on('click', handleMapClick);

        // Configurar formulario
        document.getElementById('route-form').addEventListener('submit', handleRouteSubmit);
    }

    let clickCount = 0;
    function handleMapClick(e) {
        const lat = e.latlng.lat;
        const lng = e.latlng.lng;

        if (clickCount === 0) {
            // Primer clic - origen
            document.getElementById('start-lat').value = lat.toFixed(6);
            document.getElementById('start-lng').value = lng.toFixed(6);
            addMarker([lat, lng], 'Origen');
            clickCount++;
        } else {
            // Segundo clic - destino
            document.getElementById('end-lat').value = lat.toFixed(6);
            document.getElementById('end-lng').value = lng.toFixed(6);
            addMarker([lat, lng], 'Destino');
            clickCount = 0;
        }
    }

    function addMarker(latlng, label) {
        const marker = L.marker(latlng).addTo(map);
        marker.bindPopup(label);
        markers.push(marker);
    }

    function clearMap() {
        markers.forEach(marker => map.removeLayer(marker));
        markers = [];
        if (routeLayer) {
            routeLayer.clearLayers();
        }
    }

    async function handleRouteSubmit(e) {
        e.preventDefault();
        
        const startLat = document.getElementById('start-lat').value;
        const startLng = document.getElementById('start-lng').value;
        const endLat = document.getElementById('end-lat').value;
        const endLng = document.getElementById('end-lng').value;

        try {
            // Limpiar mapa previo
            clearMap();

            // Añadir marcadores de origen y destino
            addMarker([startLat, startLng], 'Origen');
            addMarker([endLat, endLng], 'Destino');

            const response = await fetch(
                `/api/route/calculate?start_lat=${startLat}&start_lng=${startLng}&end_lat=${endLat}&end_lng=${endLng}`
            );

            if (!response.ok) {
                throw new Error('Error al calcular la ruta');
            }

            const routeFeature = await response.json();

            // Dibujar ruta
            const route = L.geoJSON(routeFeature, {
                style: {
                    color: '#3388ff',
                    weight: 5,
                    opacity: 0.65
                }
            }).addTo(routeLayer);

            // Ajustar vista
            map.fitBounds(route.getBounds(), { padding: [50, 50] });

            // Mostrar información
            document.getElementById('route-info').innerHTML = `
                <h3>Información de la ruta:</h3>
                <p>Distancia total: ${routeFeature.properties.length_km.toFixed(2)} km</p>
                <p>Nodo inicio: ${routeFeature.properties.start_node}</p>
                <p>Nodo fin: ${routeFeature.properties.end_node}</p>
            `;

        } catch (error) {
            console.error('Error:', error);
            document.getElementById('route-info').innerHTML = `
                <p class="error">Error: ${error.message}</p>
            `;
        }
    }

    // Inicializar cuando el DOM esté listo
    document.addEventListener('DOMContentLoaded', initMap);
})();