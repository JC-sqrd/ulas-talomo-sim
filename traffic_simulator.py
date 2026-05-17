import simpy
import random
import numpy as np

class TrafficSimulation:
    def __init__(self, env, crimson_coords, blue_coords, hypo_coords, spawn_rate=2.0):
        self.env = env
        self.crimson_coords = crimson_coords
        self.blue_coords = blue_coords
        self.hypo_coords = hypo_coords  # New hypothetical route
        self.spawn_rate = spawn_rate 
        
        # Performance Tracking Metrics expanded to 3 routes
        self.stats = {
            'crimson': {'count': 0, 'times': [], 'speeds': []},
            'blue': {'count': 0, 'times': [], 'speeds': []},
            'hypo': {'count': 0, 'times': [], 'speeds': []}
        }
        
        # Calculate real physical distances (meters)
        self.crimson_length = self._calculate_path_distance(crimson_coords)
        self.blue_length = self._calculate_path_distance(blue_coords)
        self.hypo_length = self._calculate_path_distance(hypo_coords)
        
        print(f"\n[Engine Initialized] Path Lengths:")
        print(f" -> Real Flyover Alignment (Crimson): {self.crimson_length:.2f}m")
        print(f" -> Ground Street Mesh (Blue)       : {self.blue_length:.2f}m")
        print(f" -> Hypothetical Flyover (Green)   : {self.hypo_length:.2f}m")

    def _calculate_path_distance(self, coords):
        total_dist = 0.0
        for i in range(len(coords) - 1):
            lat1, lon1 = np.radians(coords[i])
            lat2, lon2 = np.radians(coords[i+1])
            dlat = lat2 - lat1
            dlon = lon2 - lon1
            a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
            c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))
            total_dist += 6371000 * c 
        return total_dist

    def vehicle_process(self, vehicle_id, route_type):
        start_time = self.env.now
        
        if route_type == 'crimson':
            base_speed = random.normalvariate(16.6, 2.0)  # ~60 kph
            base_speed = max(11.1, base_speed)
            travel_time = self.crimson_length / base_speed
            stochastic_delay = np.random.exponential(scale=2.0) if random.random() > 0.8 else 0
            yield self.env.timeout(travel_time + stochastic_delay)
            
            self.stats['crimson']['count'] += 1
            self.stats['crimson']['times'].append(self.env.now - start_time)
            self.stats['crimson']['speeds'].append(base_speed * 3.6)
            
        elif route_type == 'hypo':
            # Hypothetical Flyover: Same high speed, but down a shorter, straight physical track
            base_speed = random.normalvariate(16.6, 2.0)  # ~60 kph
            base_speed = max(11.1, base_speed)
            travel_time = self.hypo_length / base_speed
            # Perfect world: zero structure friction delays
            yield self.env.timeout(travel_time)
            
            self.stats['hypo']['count'] += 1
            self.stats['hypo']['times'].append(self.env.now - start_time)
            self.stats['hypo']['speeds'].append(base_speed * 3.6)
            
        else:
            base_speed = random.normalvariate(8.3, 1.5)   # ~30 kph
            base_speed = max(4.0, base_speed)
            travel_time = self.blue_length / base_speed
            stochastic_delay = np.random.exponential(scale=15.0) if random.random() > 0.5 else np.random.exponential(scale=4.0)
            yield self.env.timeout(travel_time + stochastic_delay)
            
            self.stats['blue']['count'] += 1
            self.stats['blue']['times'].append(self.env.now - start_time)
            self.stats['blue']['speeds'].append(base_speed * 3.6)

    def vehicle_generator(self):
        vehicle_id = 0
        while True:
            yield self.env.timeout(random.expovariate(self.spawn_rate))
            vehicle_id += 1
            self.env.process(self.vehicle_process(vehicle_id, 'crimson'))
            self.env.process(self.vehicle_process(vehicle_id, 'blue'))
            self.env.process(self.vehicle_process(vehicle_id, 'hypo'))

    def run_reporting_dashboard(self):
        print("\n" + "="*50)
        print("         SIMULATION RUN SUMMARY REPORT          ")
        print("="*50)
        
        routes_to_print = [
            ('crimson', 'Real Flyover Vector (Crimson)'),
            ('hypo', 'Hypothetical Straight Flyover (Green)'),
            ('blue', 'A* Ground Optimization (Blue)')
        ]
        
        for route_key, name in routes_to_print:
            times = self.stats[route_key]['times']
            speeds = self.stats[route_key]['speeds']
            count = self.stats[route_key]['count']
            
            if count > 0:
                print(f"\nRoute: {name}")
                print(f" -> Total Sample Vehicles Concluded: {count}")
                print(f" -> Average Calculated Travel Time : {np.mean(times):.2f} seconds")
                print(f" -> Maximum Bottleneck Delay Time  : {np.max(times):.2f} seconds")
                print(f" -> Real Operational Velocity Speed: {np.mean(speeds):.2f} kph")
        print("="*50 + "\n")