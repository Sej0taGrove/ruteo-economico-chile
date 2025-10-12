const https = require('https');
const fs = require('fs');
const path = require('path');

const API_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJjbGllbnQiOiJTZWJhc3RpYW4gRXNwaW5vemEgVGFwaWEiLCJwbGFuIjoiZnJlZSIsImFkZG9ucyI6IiIsImV4Y2x1ZGVzIjoiIiwicmF0ZSI6IjV4MTAiLCJjdXN0b20iOnsiZG9jdW1lbnRfbnVtYmVyX2RhaWx5X2xpbWl0IjowLCJwbGF0ZXNfZGFpbHlfbGltaXQiOjV9LCJpYXQiOjE3NjAxNDU1OTIsImV4cCI6MTc2MjczNzU5Mn0.FJwnGxCiitGA1zSqlCy1TRtQ89A1mRhwazl4IYLGXbg';
const BASE_URL = 'api.boostr.cl';

const patentesEjemplo = ['KSLS76', 'SHVK45', 'TSTL65'];

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
                } catch {
                    reject();
                }
            });
        });

        req.on('error', () => {
            reject();
        });

        req.end();
    });
}

async function procesarPatentes(patentes) {
    const resultados = [];
    for (const patente of patentes) {
        try {
            const resultado = await obtenerDatosVehiculo(patente);
            resultados.push(resultado);
        } catch {}
    }
    return resultados;
}

function guardarJSON(data) {
    const timestamp = new Date().toISOString().split('T')[0];
    const filename = path.join('..', 'database', `vehiculos_metadata_${timestamp}.json`);
    const metadata = {
        fecha_extraccion: new Date().toISOString(),
        total_vehiculos: data.length,
        vehiculos: data
    };
    fs.writeFileSync(filename, JSON.stringify(metadata, null, 2));
}

async function main() {
    const resultados = await procesarPatentes(patentesEjemplo);
    guardarJSON(resultados);
}

main();
