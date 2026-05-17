import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
import osmnx as ox
from shapely.geometry import box

class GridFactory:
    def __init__(self, rows=300, cols=300):
        self.rows = rows
        self.cols = cols
        # Default cost landscape: Open Land = 5.0
        self.grid = np.full((self.rows, self.cols), 5.0)
        
        # Bounding box limits comfortably surrounding your new coordinates
        self.north = 7.0590
        self.south = 7.0430
        self.east = 125.5545
        self.west = 125.5410
        
    def fetch_spatial_data(self):
        print(f"Connecting to OSM Overpass API... Initializing high-res matrix ({self.rows}x{self.cols}).")
        
        ox.settings.timeout = 15
        ox.settings.use_cache = True
        ox.settings.log_console = True  # Keep logging active so you can watch it succeed!
        
        # FIXED: Rearranged to strictly follow OSMnx v2.0 order: (min_x, min_y, max_x, max_y)
        # matches: (west, south, east, north)
        bbox_tuple = (self.west, self.south, self.east, self.north)
        
        try:
            print(f"Downloading localized road networks for Davao Corridor {bbox_tuple}...")
            graph = ox.graph_from_bbox(bbox=bbox_tuple, network_type="drive")
            _, roads_gdf = ox.graph_to_gdfs(graph, nodes=True, edges=True)
            
            print("Downloading building footprints...")
            buildings_gdf = ox.features_from_bbox(bbox=bbox_tuple, tags={"building": True})
        except Exception as e:
            print(f"\n[OSM Network Error] Could not fetch live layers: {e}")
            print("Building a high-res synthetic placeholder grid to ensure project executes...")
            self._generate_synthetic_landscape()
            return self.grid

        print("Data fetched successfully! Rasterizing matrix layers...")
        
        lat_step = (self.north - self.south) / self.rows
        lon_step = (self.east - self.west) / self.cols
        
        roads_sindex = roads_gdf.sindex if not roads_gdf.empty else None
        buildings_sindex = buildings_gdf.sindex if not buildings_gdf.empty else None
        
        for r in range(self.rows):
            for c in range(self.cols):
                cell_south = self.south + (r * lat_step)
                cell_north = cell_south + lat_step
                cell_west = self.west + (c * lon_step)
                cell_east = cell_west + lon_step
                
                cell_poly = box(cell_west, cell_south, cell_east, cell_north)
                
                if buildings_sindex is not None:
                    possible_matches = buildings_sindex.query(cell_poly, predicate="intersects")
                    if len(possible_matches) > 0:
                        self.grid[r, c] = 100.0  
                        continue
                
                if roads_sindex is not None:
                    possible_roads = roads_sindex.query(cell_poly, predicate="intersects")
                    if len(possible_roads) > 0:
                        self.grid[r, c] = 1.0   
                        
        print("Rasterization complete!")
        return self.grid

    def _generate_synthetic_landscape(self):
        """Fallback landscape generator."""
        for i in range(self.rows):
            j = int(i * 0.8 + 25) 
            if 0 <= j < self.cols:
                self.grid[i, j] = 1.0