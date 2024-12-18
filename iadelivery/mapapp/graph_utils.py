import json
import os
import math

def load_graph():
    file_path = os.path.join(os.path.dirname(__file__), "distancias_provincias.json")
    with open(file_path, 'r', encoding='utf-8') as file:
        return json.load(file)

def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371.0
    import math
    dLat = math.radians(lat2 - lat1)
    dLon = math.radians(lon2 - lon1)
    a = (math.sin(dLat/2)**2) + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * (math.sin(dLon/2)**2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    distance = R * c
    return distance
