"""Datos de ejemplo (ficticios) para llenar la base de datos la primera vez.

Las paradas de cada ruta están en el orden del recorrido.
Las coordenadas son aproximadas y solo sirven para mostrar las paradas en el mapa.
"""

# Parada -> (latitud, longitud)
COORDENADAS = {
    "Niquía": (6.3373, -75.5440),
    "Parque de Bello": (6.3366, -75.5578),
    "Madera": (6.3155, -75.5547),
    "Caribe": (6.2775, -75.5698),
    "Universidad de Antioquia": (6.2675, -75.5688),
    "Parque Berrío": (6.2502, -75.5683),
    "San Antonio": (6.2470, -75.5698),
    "Parque de Copacabana": (6.3466, -75.5089),
    "Autopista Norte": (6.3440, -75.5250),
    "Exposiciones": (6.2395, -75.5713),
    "Poblado": (6.2125, -75.5780),
    "Aguacatala": (6.1935, -75.5822),
    "Envigado": (6.1717, -75.5874),
    "Parque de Itagüí": (6.1719, -75.6116),
    "Estadio": (6.2528, -75.5877),
    "Laureles": (6.2453, -75.5966),
    "Floresta": (6.2585, -75.6022),
}

RUTAS = [
    {
        "codigo": "R01",
        "nombre": "Bello – Centro",
        "recorrido": "Sale de Niquía, baja por la Autopista Norte y termina en San Antonio.",
        "horario": "4:30 a. m. – 10:30 p. m.",
        "frecuencia": 10,
        "paradas": ["Niquía", "Parque de Bello", "Madera", "Caribe", "Universidad de Antioquia", "Parque Berrío", "San Antonio"],
    },
    {
        "codigo": "R02",
        "nombre": "Copacabana – Bello",
        "recorrido": "Conecta el parque de Copacabana con el centro de Bello por la Autopista Norte.",
        "horario": "5:00 a. m. – 9:30 p. m.",
        "frecuencia": 15,
        "paradas": ["Parque de Copacabana", "Autopista Norte", "Niquía", "Parque de Bello"],
    },
    {
        "codigo": "R03",
        "nombre": "Centro – Poblado – Envigado",
        "recorrido": "Sale de San Antonio hacia el sur por la Avenida El Poblado hasta Envigado.",
        "horario": "5:00 a. m. – 11:00 p. m.",
        "frecuencia": 8,
        "paradas": ["San Antonio", "Exposiciones", "Poblado", "Aguacatala", "Envigado"],
    },
    {
        "codigo": "R04",
        "nombre": "Itagüí – Centro",
        "recorrido": "Une el parque de Itagüí con el centro pasando por Exposiciones.",
        "horario": "4:45 a. m. – 10:00 p. m.",
        "frecuencia": 12,
        "paradas": ["Parque de Itagüí", "Aguacatala", "Exposiciones", "San Antonio", "Parque Berrío"],
    },
    {
        "codigo": "R05",
        "nombre": "Circular Estadio – Laureles",
        "recorrido": "Recorrido circular por el occidente: Universidad de Antioquia, Estadio, Laureles y Floresta.",
        "horario": "6:00 a. m. – 9:00 p. m.",
        "frecuencia": 20,
        "paradas": ["Universidad de Antioquia", "Estadio", "Laureles", "Floresta", "Caribe"],
    },
]
