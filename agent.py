from collections import deque
import heapq
import math

from logic_engine import KnowledgeBase

STEP_ACTIONS = {
    (0, 1): 'Up',
    (0, -1): 'Down',
    (-1, 0): 'Left',
    (1, 0): 'Right',
}


class SearchAgent:
    
    def __init__(self, active_algo='BFS'):
        self.plan = []
        self.active_algo = active_algo

        # Lab 07: Knowledge Base holding the game's safety rules (Horn clauses)
        self.kb = KnowledgeBase()
        # Rule 1: TargetVisible AND HasDust => SafeToEngage
        self.kb.tell_rule(['TargetVisible', 'HasDust'], 'SafeToEngage')
        # Rule 2: SafeToEngage AND BloodseekerMissing => Retreat
        self.kb.tell_rule(['SafeToEngage', 'BloodseekerMissing'], 'Retreat')

    
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
            elif self.active_algo == 'A*':
                
                tile_facts = {
                    (1, 0): ['TargetVisible', 'HasDust', 'BloodseekerMissing'],  
                    (0, 1): ['TargetVisible', 'HasDust'],                        
                }
                self.plan = self.astar_search(start, goal, walls, grid, tile_facts=tile_facts)

                
                if not self.plan:
                    for other in sorted(foods, key=lambda f: self.manhattan_distance(start, f)):
                        if other == goal:
                            continue
                        self.plan = self.astar_search(start, other, walls, grid, tile_facts=tile_facts)
                        if self.plan:
                            break
            else:
                self.plan = self.bfs_search(start, goal, walls, grid)

            if not self.plan:
                return 'suck'                             
        return self.plan.pop(0)                            

    
    def _closest_food(self, start, foods):
        return min(foods, key=lambda f: abs(f[0] - start[0]) + abs(f[1] - start[1]))

    def _neighbors(self, pos, walls, grid):
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

    def manhattan_distance(self, pos, goal):
        """Calculate the Manhattan distance between two positions."""
        return abs(pos[0] - goal[0]) + abs(pos[1] - goal[1])

    def euclidean_distance(self, pos, goal):
        """Calculate the Euclidean distance between two positions."""
        return math.sqrt((pos[0] - goal[0]) ** 2 + (pos[1] - goal[1]) ** 2)


    def astar_search(self, start, goal, walls, grid, heuristic_type='manhattan', tile_facts=None):
        
        if tile_facts is None:
            tile_facts = {}

        if heuristic_type == 'euclidean':
            heuristic = self.euclidean_distance
        else:
            heuristic = self.manhattan_distance
        
       
        frontier = []
        reached_states = set()
        
        
        g_cost = 0
        h_cost = heuristic(start, goal)
        f_cost = g_cost + h_cost
        heapq.heappush(frontier, (f_cost, g_cost, start, []))
        
        
        while frontier:
           
            f_cost, g_cost, pos, path = heapq.heappop(frontier)
            
            
            if pos == goal:
                return path
            
           
            if pos in reached_states:
                continue
            reached_states.add(pos)
            
          
            
            for action, npos in self._neighbors(pos, walls, grid):

                if npos not in reached_states:

                    
                    self.kb.clear_facts()                       
                    for fact in tile_facts.get(npos, []):       
                        self.kb.tell_fact(fact)
                    self.kb.forward_chain()                     
                    if 'Retreat' in self.kb.facts:              
                        continue                                

                    g_new = g_cost + 1
                    h_new = heuristic(npos, goal)
                    f_new = g_new + h_new
                    heapq.heappush(frontier, (f_new, g_new, npos, path + [action]))
        
        return []



if __name__ == "__main__":
    agent = SearchAgent()
    start_pos = (0, 0)
    goal_pos = (3, 4)
    
    manhattan = agent.manhattan_distance(start_pos, goal_pos)
    euclidean = agent.euclidean_distance(start_pos, goal_pos)
    
    print(f"Start position: {start_pos}")
    print(f"Goal position: {goal_pos}")
    print(f"Manhattan distance: {manhattan}")
    print(f"Euclidean distance: {euclidean}")
    
    # Test A* search with a simple grid
    print("\n--- A* Search Test ---")
    walls = {(1, 1), (1, 2)}
    grid_size = (5, 5)
    path = agent.astar_search(start_pos, goal_pos, walls, grid_size)
    print(f"A* Path (Manhattan heuristic): {path}")
    
    path_euclidean = agent.astar_search(start_pos, goal_pos, walls, grid_size, heuristic_type='euclidean')
    print(f"A* Path (Euclidean heuristic): {path_euclidean}")
