# agent.py  -  Lab 03: Uninformed Search (BFS / DFS / UCS)
from collections import deque
import heapq

STEP_ACTIONS = {
    (0, 1): 'Up',
    (0, -1): 'Down',
    (-1, 0): 'Left',
    (1, 0): 'Right',
}


class SearchAgent:
    """A goal-based PLANNING agent.

    Instead of reacting to one cell at a time, it uses the world model exposed in
    the percept (grid size, walls, all food) to SEARCH offline for a full path to
    the nearest food, stores that path in self.plan, then plays it back one action
    per tick. Switch self.active_algo between 'BFS', 'DFS', 'UCS' to compare them.
    """

    def __init__(self, active_algo='BFS'):
        self.plan = []                 
        self.active_algo = active_algo 

    
    def sense_and_act(self, percept: dict) -> str:
        if not self.plan:                                  
            start = tuple(percept['agent_pos'])
            foods = [tuple(f) for f in percept['all_food']]
            if not foods:
                return 'suck'                              
            walls = set(tuple(w) for w in percept['walls'])
            grid = percept['grid_size']
            goal = self._closest_food(start, foods)

            if self.active_algo == 'DFS':
                self.plan = self.dfs_search(start, goal, walls, grid)
            elif self.active_algo == 'UCS':
                self.plan = self.ucs_search(start, goal, walls, grid)
            else:
                self.plan = self.bfs_search(start, goal, walls, grid)

            if not self.plan:
                return 'suck'                             
        return self.plan.pop(0)                            

    
    def _closest_food(self, start, foods):
        """Pick the food with the smallest Manhattan distance to the agent."""
        return min(foods, key=lambda f: abs(f[0] - start[0]) + abs(f[1] - start[1]))

    def _neighbors(self, pos, walls, grid):
        """Legal 4-connected moves from pos as (action, new_pos) pairs."""
        w, h = grid
        x, y = pos
        out = []
        for (dx, dy), action in STEP_ACTIONS.items():
            nx, ny = x + dx, y + dy
            if 0 <= nx < w and 0 <= ny < h and (nx, ny) not in walls:
                out.append((action, (nx, ny)))
        return out

    
    def bfs_search(self, start, goal, walls, grid):
        frontier = deque([(start, [])])
        reached = {start}                                 
        while frontier:
            pos, path = frontier.popleft()                 
            if pos == goal:
                return path
            for action, npos in self._neighbors(pos, walls, grid):
                if npos not in reached:
                    reached.add(npos)
                    frontier.append((npos, path + [action]))
        return []                                          # goal unreachable

    
    def dfs_search(self, start, goal, walls, grid):
        frontier = [(start, [])]
        reached = {start}
        while frontier:
            pos, path = frontier.pop()                     
            if pos == goal:
                return path
            for action, npos in self._neighbors(pos, walls, grid):
                if npos not in reached:
                    reached.add(npos)
                    frontier.append((npos, path + [action]))
        return []

    
    def ucs_search(self, start, goal, walls, grid):
        counter = 0                                        
        frontier = [(0, counter, start, [])]               
        best = {start: 0}
        while frontier:
            cost, _, pos, path = heapq.heappop(frontier)   
            if pos == goal:
                return path
            for action, npos in self._neighbors(pos, walls, grid):
                new_cost = cost + 1                        
                if npos not in best or new_cost < best[npos]:
                    best[npos] = new_cost
                    counter += 1
                    heapq.heappush(frontier, (new_cost, counter, npos, path + [action]))
        return []
