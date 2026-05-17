import heapq
import numpy as np

class AStarPathfinder:
    def __init__(self, grid_matrix):
        self.grid = grid_matrix
        self.rows = grid_matrix.shape[0]
        self.cols = grid_matrix.shape[1]

    def _heuristic(self, node, goal):
        # High-speed Euclidean distance calculation
        return np.sqrt((node[0] - goal[0])**2 + (node[1] - goal[1])**2)

    def find_path(self, start, goal):
        open_set = []
        heapq.heappush(open_set, (0, start))
        came_from = {}
        
        # Performance Boost: Using a flat infinity array instead of a slow dictionary loop
        g_score = np.full((self.rows, self.cols), float('inf'))
        g_score[start] = 0.0
        
        # 8-Directional Movement Vectors (Orthogonal + Diagonal)
        neighbors = [(-1,0), (1,0), (0,-1), (0,1), (-1,-1), (-1,1), (1,-1), (1,1)]
        
        while open_set:
            _, current = heapq.heappop(open_set)
            
            if current == goal:
                path = []
                while current in came_from:
                    path.append(current)
                    current = came_from[current]
                path.append(start)
                return path[::-1]
                
            for dr, dc in neighbors:
                nr, nc = current[0] + dr, current[1] + dc
                
                # Boundary safety check
                if 0 <= nr < self.rows and 0 <= nc < self.cols:
                    move_cost = self.grid[nr, nc]
                    
                    # Apply a 1.414 penalty for diagonal steps to ensure realistic steering geometry
                    if dr != 0 and dc != 0:
                        move_cost *= 1.41421356
                        
                    tentative_g = g_score[current[0], current[1]] + move_cost
                    
                    if tentative_g < g_score[nr, nc]:
                        came_from[(nr, nc)] = current
                        g_score[nr, nc] = tentative_g
                        f_score = tentative_g + self._heuristic((nr, nc), goal)
                        heapq.heappush(open_set, (f_score, (nr, nc)))
                        
        return [] # Return empty list if a physical obstacle blocks the corridor completely