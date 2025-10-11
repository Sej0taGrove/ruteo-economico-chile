// extract_vehiculos.js
// Extractor de datos de vehículos desde Booster API por patente

const https = require('https');
const fs = require('fs');

// Configuración de la API
const API_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJjbGllbnQiOiJTZWJhc3RpYW4gRXNwaW5vemEgVGFwaWEiLCJwbGFuIjoiZnJlZSIsImFkZG9ucyI6IiIsImV4Y2x1ZGVzIjoiIiwicmF0ZSI6IjV4MTAiLCJjdXN0b20iOnsiZG9jdW1lbnRfbnVtYmVyX2RhaWx5X2xpbWl0IjowLCJwbGF0ZXNfZGFpbHlfbGltaXQiOjV9LCJpYXQiOjE3NjAxNDU1OTIsImV4cCI6MTc2MjczNzU5Mn0.FJwnGxCiitGA1zSqlCy1TRtQ89A1mRhwazl4IYLGXbg'; // Reemplaza con tu API key real
const BASE_URL = 'api.boostr.cl';

// Patentes de ejemplo para pruebas (usuarios pueden ingresar estas)
const patentesEjemplo = ['KSLS76', 'SHVK45', 'TSTL65']; 

// Función para obtener datos de un vehículo específico
function obtenerDatosVehiculo(patente) {
    return new Promise((resolve, reject) => {
        const options = {
            hostname: BASE_URL,
            path: `/vehicle/${patente}.json`,
            method: 'GET',
            headers: {
                'X-API-KEY': API_KEY,
                'accept': 'application/json'
            }
        };

        const req = https.request(options, (res) => {
            let data = '';
            
            res.on('data', (chunk) => {
                data += chunk;
            });
            
            res.on('end', () => {
                try {
                    const jsonData = JSON.parse(data);
                    resolve({ patente, data: jsonData });
                } catch (error) {
                    reject(`Error al parsear JSON para ${patente}: ${error}`);
                }
            });
        });
        
        req.on('error', (error) => {
            reject(`Error en petición para ${patente}: ${error}`);
        });
        
        req.end();
    });
}

// Función para procesar múltiples patentes
async function procesarPatentes(patentes) {
    const resultados = [];
    
    for (const patente of patentes) {
        try {
            console.log(`Consultando patente: ${patente}...`);
            const resultado = await obtenerDatosVehiculo(patente);
            resultados.push(resultado);
        } catch (error) {
            console.error(`Error con patente ${patente}:`, error);
        }
    }
    
    return resultados;
}

// Función para guardar el JSON consolidado
function guardarJSON(data) {
    const timestamp = new Date().toISOString().split('T')[0];
    const filename = `vehiculos_metadata_${timestamp}.json`;
    
    const metadata = {
        fecha_extraccion: new Date().toISOString(),
        total_vehiculos: data.length,
        vehiculos: data
    };
    
    fs.writeFileSync(filename, JSON.stringify(metadata, null, 2));
    console.log(`Datos consolidados guardados en: ${filename}`);
}

// Función principal
async function main() {
    console.log('=== Extractor de Metadata de Vehículos ===');
    console.log('Iniciando extracción de datos de vehículos...');
    
    try {
        const resultados = await procesarPatentes(patentesEjemplo);
        guardarJSON(resultados);
        
        console.log(`\nExtracción completada. Total vehículos procesados: ${resultados.length}`);
    } catch (error) {
        console.error('Error en proceso principal:', error);
    }
}

// Ejecutar
main();
