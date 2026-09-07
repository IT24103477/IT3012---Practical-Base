# visual_grid_game.py
import random
import tkinter as tk
from agent import SearchAgent          

DIRECTIONS = [(0, 1), (1, 0), (0, -1), (-1, 0)]
DIR_NAMES = ['N', 'E', 'S', 'W']
DIR_INDEX = {'Up': 0, 'Right': 1, 'Down': 2, 'Left': 3}


class VisualGridHuntGame:
    """Grid environment. For Lab 03 the percept now exposes the full world model
    (grid size, walls, all food) so a search agent can plan a path offline."""

    def __init__(self, width=10, height=10, num_food=10, num_opponents=2,
                 custom_walls=None, max_steps=60):
        self.width = width
        self.height = height
        self.agent_pos = [0, 0]
        self.heading = 0
        self.max_steps = max_steps

        if custom_walls is not None:
            self.walls = set(custom_walls)
        else:
            self.walls = {(2, 2), (2, 3), (5, 5), (6, 5), (3, 7)}

        self.food_positions = set()
        while len(self.food_positions) < num_food:
            fx = random.randint(0, self.width - 1)
            fy = random.randint(0, self.height - 1)
            pos = (fx, fy)
            if pos != (0, 0) and pos not in self.walls:
                self.food_positions.add(pos)

        self.toxic_traps = set()
        while len(self.toxic_traps) < 3:
            tx = random.randint(0, self.width - 1)
            ty = random.randint(0, self.height - 1)
            trap = (tx, ty)
            if trap != (0, 0) and trap not in self.walls and trap not in self.food_positions:
                self.toxic_traps.add(trap)

        self.opponents = []
        while len(self.opponents) < num_opponents:
            ox = random.randint(0, self.width - 1)
            oy = random.randint(0, self.height - 1)
            op = [ox, oy]
            if tuple(op) != (0, 0) and tuple(op) not in self.walls and tuple(op) not in self.food_positions:
                self.opponents.append(op)

        self.score = 0
        self.steps = 0
        self.collision = False

    def _cell_blocked(self, cell):
        x, y = cell
        if x < 0 or x >= self.width or y < 0 or y >= self.height:
            return True
        return cell in self.walls

  
    def get_percept(self) -> dict:
        dx, dy = DIRECTIONS[self.heading]
        front = (self.agent_pos[0] + dx, self.agent_pos[1] + dy)
        return {
            'agent_pos': list(self.agent_pos),          
            'food_here': tuple(self.agent_pos) in self.food_positions,
            'wall_ahead': self._cell_blocked(front),
            'toxin_here': tuple(self.agent_pos) in self.toxic_traps,
            'grid_size': (self.width, self.height),     
            'walls': list(self.walls),                  
            'all_food': list(self.food_positions),     
        }

    
    def execute_action(self, action: str):
        self.steps += 1

        
        if action in DIR_INDEX:
            idx = DIR_INDEX[action]
            self.heading = idx                          
            dx, dy = DIRECTIONS[idx]
            new = (self.agent_pos[0] + dx, self.agent_pos[1] + dy)
            if self._cell_blocked(new):
                self.score -= 5
            else:
                self.agent_pos = [new[0], new[1]]
                if new in self.toxic_traps:
                    self.score -= 15
                if tuple(self.agent_pos) in self.food_positions:   
                    self.food_positions.remove(tuple(self.agent_pos))
                    self.score += 20

        
        elif action == 'turn_left':
            self.heading = (self.heading - 1) % 4
        elif action == 'turn_right':
            self.heading = (self.heading + 1) % 4
        elif action == 'move_forward':
            dx, dy = DIRECTIONS[self.heading]
            new = (self.agent_pos[0] + dx, self.agent_pos[1] + dy)
            if self._cell_blocked(new):
                self.score -= 5
            else:
                self.agent_pos = [new[0], new[1]]
                if new in self.toxic_traps:
                    self.score -= 15
        elif action == 'suck':
            pos = tuple(self.agent_pos)
            if pos in self.food_positions:
                self.food_positions.remove(pos)
                self.score += 20

        for op in self.opponents:
            move = random.choice(['Up', 'Down', 'Left', 'Right', 'Stay'])
            if move == 'Up' and op[1] < self.height - 1:
                op[1] += 1
            elif move == 'Down' and op[1] > 0:
                op[1] -= 1
            elif move == 'Left' and op[0] > 0:
                op[0] -= 1
            elif move == 'Right' and op[0] < self.width - 1:
                op[0] += 1
            if op == self.agent_pos:
                self.score -= 50
                self.collision = True

    def is_done(self) -> bool:
        return len(self.food_positions) == 0 or self.steps >= self.max_steps or self.collision


class GridGameGUI:
    """Tkinter wrapper. Driven by an agent's sense_and_act()."""

    def __init__(self, root, agent, width=10, height=10, num_food=12,
                 num_opponents=2, walls=None, max_steps=60):
        self.root = root
        self.root.title("IT3012 - Search Agent Grid Hunt")
        self.agent = agent

        self.env = VisualGridHuntGame(width=width, height=height, num_food=num_food,
                                      num_opponents=num_opponents, custom_walls=walls,
                                      max_steps=max_steps)

        max_canvas_dim = 600
        self.cell_size = max(20, min(max_canvas_dim // self.env.width, max_canvas_dim // self.env.height))
        canvas_w = self.env.width * self.cell_size
        canvas_h = self.env.height * self.cell_size

        self.canvas = tk.Canvas(root, width=canvas_w, height=canvas_h, bg="white")
        self.canvas.pack()

        self.label = tk.Label(root, text="Score: 0 | Steps: 0", font=("Arial", 14))
        self.label.pack(pady=10)

        self.btn = tk.Button(root, text="Start Simulation", command=self.run_loop,
                             font=("Arial", 12), bg="#000066", fg="white")
        self.btn.pack(pady=5)

        
        self.trail = []
        self.draw_grid()

    def draw_grid(self):
        self.canvas.delete("all")

        for x in range(self.env.width):
            for y in range(self.env.height):
                x1 = x * self.cell_size
                y1 = (self.env.height - 1 - y) * self.cell_size
                color = "#f1f5f9" if (x, y) not in self.env.walls else "#64748b"
                self.canvas.create_rectangle(x1, y1, x1 + self.cell_size, y1 + self.cell_size,
                                             fill=color, outline="#cbd5e1")
                if self.cell_size >= 40 and (x, y) in self.env.walls:
                    self.canvas.create_text(x1 + self.cell_size / 2, y1 + self.cell_size / 2,
                                            text="W", fill="white", font=("Arial", 8, "bold"))

        
        for (tx, ty) in self.trail:
            x1 = tx * self.cell_size + self.cell_size * 0.35
            y1 = (self.env.height - 1 - ty) * self.cell_size + self.cell_size * 0.35
            self.canvas.create_oval(x1, y1, x1 + self.cell_size * 0.3, y1 + self.cell_size * 0.3,
                                    fill="#c7d2fe", outline="")

        for fx, fy in self.env.food_positions:
            off = self.cell_size * 0.25
            x1 = fx * self.cell_size + off
            y1 = (self.env.height - 1 - fy) * self.cell_size + off
            self.canvas.create_oval(x1, y1, x1 + self.cell_size * 0.5, y1 + self.cell_size * 0.5,
                                    fill="#f59e0b", outline="#d97706")

        for ox, oy in self.env.opponents:
            off = self.cell_size * 0.2
            x1 = ox * self.cell_size + off
            y1 = (self.env.height - 1 - oy) * self.cell_size + off
            self.canvas.create_rectangle(x1, y1, x1 + self.cell_size * 0.6, y1 + self.cell_size * 0.6,
                                         fill="#990000", outline="#7a0000")

        for tx, ty in self.env.toxic_traps:
            off = self.cell_size * 0.25
            x1 = tx * self.cell_size + off
            y1 = (self.env.height - 1 - ty) * self.cell_size + off
            self.canvas.create_oval(x1, y1, x1 + self.cell_size * 0.5, y1 + self.cell_size * 0.5,
                                    fill="purple")

        ax, ay = self.env.agent_pos
        off = self.cell_size * 0.15
        x1 = ax * self.cell_size + off
        y1 = (self.env.height - 1 - ay) * self.cell_size + off
        self.canvas.create_oval(x1, y1, x1 + self.cell_size * 0.7, y1 + self.cell_size * 0.7,
                                fill="#000066", outline="#1e3a8a")

    def run_loop(self):
        self.btn.config(state="disabled")

        def step():
            if not self.env.is_done():
                action = self.agent.sense_and_act(self.env.get_percept())
                self.env.execute_action(action)
                self.trail.append(tuple(self.env.agent_pos))
                self.draw_grid()
                self.label.config(text=f"Score: {self.env.score} | Steps: {self.env.steps} | Action: {action}")
                self.root.after(120, step)
            else:
                end = (f"Collision! Game Over! Final Score: {self.env.score}"
                       if self.env.collision else f"Finished! Final Score: {self.env.score}")
                self.label.config(text=end)
                self.btn.config(state="normal")

        step()


if __name__ == "__main__":
    
    ACTIVE_ALGO = "A*"

    agent = SearchAgent(active_algo=ACTIVE_ALGO)

    my_walls = {(1, 1), (1, 2), (2, 1), (3, 3), (4, 4), (5, 5), (6, 6), (7, 7)}

    root = tk.Tk()
    app = GridGameGUI(root, agent=agent, width=12, height=12, num_food=15,
                      num_opponents=0,max_steps=500, walls=my_walls)
    root.mainloop()
