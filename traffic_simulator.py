import simpy
import random
import numpy as np

class TrafficSimulation:
    def __init__(self, env, crimson_coords, blue_coords, spawn_rate=2.0):
        self.env = env
        self.crimson_coords = crimson_coords
        self.blue_coords = blue_coords
        self.spawn_rate = spawn_rate  # Average vehicles spawned per second
        
        # Performance Tracking Metrics
        self.stats = {
            'crimson': {'count': 0, 'times': [], 'speeds': []},
            'blue': {'count': 0, 'times': [], 'speeds': []}
        }
        
        # Calculate real physical distances (meters) using simple Haversine approximation
        self.crimson_length = self._calculate_path_distance(crimson_coords)
        self.blue_length = self._calculate_path_distance(blue_coords)
        
        print(f"\n[Engine Initialized] Path Lengths -> Flyover (Crimson): {self.crimson_length:.2f}m | Ground Mesh (Blue): {self.blue_length:.2f}m")

    def _calculate_path_distance(self, coords):
        """Calculates total path distance in meters across coordinate chains."""
        total_dist = 0.0
        for i in range(len(coords) - 1):
            lat1, lon1 = np.radians(coords[i])
            lat2, lon2 = np.radians(coords[i+1])
            dlat = lat2 - lat1
            dlon = lon2 - lon1
            a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
            c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))
            total_dist += 6371000 * c  # Earth radius in meters
        return total_dist

    def vehicle_process(self, vehicle_id, route_type):
        """Simpy Process representing an isolated vehicle traveling down a selected track."""
        start_time = self.env.now
        
        if route_type == 'crimson':
            # Flyover properties: Fast, free-flowing, minimal variance
            base_speed = random.normalvariate(16.6, 2.0)  # ~60 kph converted to m/s
            base_speed = max(11.1, base_speed)           # Floor at 40 kph
            travel_time = self.crimson_length / base_speed
            
            # Minor stochastic delay for braking wave phenomena
            stochastic_delay = np.random.exponential(scale=2.0) if random.random() > 0.8 else 0
            yield self.env.timeout(travel_time + stochastic_delay)
            
            end_time = self.env.now
            self.stats['crimson']['count'] += 1
            self.stats['crimson']['times'].append(end_time - start_time)
            self.stats['crimson']['speeds'].append(base_speed * 3.6)
            
        else:
            # Street-level A* properties: Slower, high density, unpredictable friction elements
            base_speed = random.normalvariate(8.3, 1.5)   # ~30 kph converted to m/s
            base_speed = max(4.0, base_speed)            # Floor at 15 kph
            travel_time = self.blue_length / base_speed
            
            # Heavy exponential congestion spikes representing traffic lights and street bottlenecks
            stochastic_delay = np.random.exponential(scale=15.0) if random.random() > 0.5 else np.random.exponential(scale=4.0)
            yield self.env.timeout(travel_time + stochastic_delay)
            
            end_time = self.env.now
            self.stats['blue']['count'] += 1
            self.stats['blue']['times'].append(end_time - start_time)
            self.stats['blue']['speeds'].append(base_speed * 3.6)

    def vehicle_generator(self):
        """Spawns vehicles continuously via a Poisson distribution interval stream."""
        vehicle_id = 0
        while True:
            # Exponential distribution defines the arrival interval gap between vehicles
            yield self.env.timeout(random.expovariate(self.spawn_rate))
            vehicle_id += 1
            
            # Send identical parallel vehicle streams down both configurations to capture benchmark delta
            self.env.process(self.vehicle_process(vehicle_id, 'crimson'))
            self.env.process(self.vehicle_process(vehicle_id, 'blue'))

    def run_reporting_dashboard(self):
        """Aggregates outputs and logs analytical telemetry metrics."""
        print("\n" + "="*50)
        print("         SIMULATION RUN SUMMARY REPORT          ")
        print("="*50)
        
        for route in ['crimson', 'blue']:
            name = "Ulas Flyover Vector (Crimson)" if route == 'crimson' else "A* Ground Optimization (Blue)"
            times = self.stats[route]['times']
            speeds = self.stats[route]['speeds']
            count = self.stats[route]['count']
            
            if count > 0:
                print(f"\nRoute: {name}")
                print(f" -> Total Sample Vehicles Concluded: {count}")
                print(f" -> Average Calculated Travel Time : {np.mean(times):.2f} seconds")
                print(f" -> Maximum Bottleneck Delay Time  : {np.max(times):.2f} seconds")
                print(f" -> Real Operational Velocity Speed: {np.mean(speeds):.2f} kph")
            else:
                print(f"\nRoute: {name} - No vehicles completed transit within the time limits.")
        print("="*50 + "\n")