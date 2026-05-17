import folium
import numpy as np
import requests
import simpy
from grid_factory import GridFactory
from pathfinder import AStarPathfinder
from traffic_simulator import TrafficSimulation

# 1. INITIALIZE SPATIAL BOUNDARIES & RASTER MESH
factory = GridFactory()
cost_surface = factory.fetch_spatial_data()

# 2. CONFIGURATION: TARGET PARAMETERS
TARGET_WAY_IDS = [1042528635, 1042528633]

REAL_START_LAT = 7.0550936
REAL_START_LON = 125.5421582

REAL_GOAL_LAT = 7.0463073
REAL_GOAL_LON = 125.5532196

# =====================================================================
# NEW: GENERATE THE HYPOTHETICAL STRAIGHT FLYOVER
# =====================================================================
# A straight path completely ignoring the grid, streets, or building layers
hypothetical_map_points = [
    [REAL_START_LAT, REAL_START_LON],
    [REAL_GOAL_LAT, REAL_GOAL_LON]
]
# =====================================================================

# 3. COORDINATE TRANSLATION CALCULATOR ENGINE
def latlon_to_grid(lat, lon, factory_obj):
    lat_range = factory_obj.north - factory_obj.south
    lon_range = factory_obj.east - factory_obj.west
    r_pct = (lat - factory_obj.south) / lat_range
    c_pct = (lon - factory_obj.west) / lon_range
    r_idx = int(np.clip(r_pct * factory_obj.rows, 0, factory_obj.rows - 1))
    c_idx = int(np.clip(c_pct * factory_obj.cols, 0, factory_obj.cols - 1))
    return (r_idx, c_idx)

def grid_to_latlon(path_nodes, factory_obj):
    latlon_coordinates = []
    lat_step = (factory_obj.north - factory_obj.south) / factory_obj.rows
    lon_step = (factory_obj.east - factory_obj.west) / factory_obj.cols
    for r, c in path_nodes:
        lat = factory_obj.south + (r * lat_step) + (lat_step / 2)
        lon = factory_obj.west + (c * lon_step) + (lon_step / 2)
        latlon_coordinates.append([lat, lon])
    return latlon_coordinates

start_node = latlon_to_grid(REAL_START_LAT, REAL_START_LON, factory)
goal_node = latlon_to_grid(REAL_GOAL_LAT, REAL_GOAL_LON, factory)

# 4. RUN ALGORITHMIC A* PATHFINDING
print("\n--- Running Node-Locked Simulation Path Analysis ---")
print("Executing A* Optimization Algorithm...")
finder = AStarPathfinder(cost_surface)
astar_grid_path = finder.find_path(start_node, goal_node)
astar_map_points = grid_to_latlon(astar_grid_path, factory)

# 5. OVERPASS DIRECT DOWNLOADER (CRIMSON PATH TRACKS)
print("Querying Overpass API for explicit node geometry of the requested Ways...")
gov_map_points = []
overpass_url = "https://overpass-api.de/api/interpreter"
overpass_query = """
[out:json][timeout:30];
(
  way(id:1042528635);
  way(id:1042528633);
);
out geom;
"""

try:
    headers = {'User-Agent': 'UlasTrafficSimulationProject/2.0'}
    response = requests.post(overpass_url, data={"data": overpass_query}, headers=headers)
    if response.status_code == 200:
        data = response.json()
        if "elements" in data and len(data["elements"]) > 0:
            for element in data["elements"]:
                if "geometry" in element:
                    for pt in element["geometry"]:
                        gov_map_points.append([pt["lat"], pt["lon"]])
except Exception as e:
    print(f"Overpass connection failed: {e}")

if not gov_map_points:
    gov_map_points = [[REAL_START_LAT, REAL_START_LON], [REAL_GOAL_LAT, REAL_GOAL_LON]]

# 6. COMPILE FOLIUM INTERACTIVE VISUAL LAYER
m = folium.Map(location=[REAL_START_LAT, REAL_START_LON], zoom_start=15, tiles="OpenStreetMap")

folium.Rectangle(bounds=[[factory.south, factory.west], [factory.north, factory.east]], color="#333333", weight=2, fill=False, dash_array='5, 5').add_to(m)
folium.Marker([REAL_START_LAT, REAL_START_LON], popup="A* Entry Node", icon=folium.Icon(color="green", icon="play")).add_to(m)
folium.Marker([REAL_GOAL_LAT, REAL_GOAL_LON], popup="A* Exit Node", icon=folium.Icon(color="black", icon="flag")).add_to(m)

# Crimson Path: Real Flyover
folium.PolyLine(locations=gov_map_points, color="#D9213D", weight=6, opacity=0.9, popup="Crimson Path: Real Planned Flyover").add_to(m)

# Royal Blue Path: A* Ground Streets
if astar_map_points:
    folium.PolyLine(locations=astar_map_points, color="#1A73E8", weight=6, opacity=0.95, popup="Royal Blue Path: A* Ground Optimization").add_to(m)

# NEW: Forest Green Path: Hypothetical Flyover
folium.PolyLine(locations=hypothetical_map_points, color="#2E7D32", weight=4, opacity=0.8, dash_array='10, 10', popup="Green Path: Hypothetical Perfect Flyover").add_to(m)

output_html = "davao_simulation_viewer.html"
m.save(output_html)
print(f"Success! Map dashboard generated as '{output_html}'.")

# 7. DISCRETE EVENT TRAFFIC SIMULATION RUNNER CHASSIS
if __name__ == "__main__":
    print("\nInitializing Stochastic Discrete Event Traffic Simulation...")
    env = simpy.Environment()
    
    if gov_map_points and astar_map_points:
        # Pass the new hypothetical coordinates into the traffic engine
        sim = TrafficSimulation(env, crimson_coords=gov_map_points, blue_coords=astar_map_points, hypo_coords=hypothetical_map_points, spawn_rate=1.5)
        env.process(sim.vehicle_generator())
        print("Simulating 3600 seconds (1 Hour) of active corridor traffic. Processing events...")
        env.run(until=3600)
        sim.run_reporting_dashboard()