# visual_grid_game.py  -  Lab 02: Simple Reflex vs Model-Based Agents
import random
import tkinter as tk


DIRECTIONS = [(0, 1), (1, 0), (0, -1), (-1, 0)]
DIR_NAMES = ['N', 'E', 'S', 'W']


class VisualGridHuntGame:
    """Partially observable grid environment. The agent has a facing direction
    and can only sense the cell it stands on and the single cell in front of it."""

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
        """A cell is blocked if it is off the grid or is a wall."""
        x, y = cell
        if x < 0 or x >= self.width or y < 0 or y >= self.height:
            return True
        return cell in self.walls

    
    def get_percept(self) -> dict:
        dx, dy = DIRECTIONS[self.heading]
        front = (self.agent_pos[0] + dx, self.agent_pos[1] + dy)
        return {
            'food_here': tuple(self.agent_pos) in self.food_positions,
            'wall_ahead': self._cell_blocked(front),
            'toxin_here': tuple(self.agent_pos) in self.toxic_traps,
        }

   
    def execute_action(self, action: str):
        self.steps += 1

        if action == 'turn_left':
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


class SimpleReflexAgent:
    """Pure condition-action rules. No __init__, no memory of the past."""

    def sense_and_act(self, percept: dict) -> str:
        if percept['food_here']:          
            return 'suck'
        elif percept['wall_ahead']:      
            return 'turn_left'
        else:                             
            return 'move_forward'


class ModelBasedAgent:
    """Maintains an internal model: its own (relative) position and heading,
    the cells it has visited, and the walls it has discovered. Uses that memory
    to avoid re-treading and to escape the loops a reflex agent falls into."""

    def __init__(self, start_heading=0):
        self.pos = (0, 0)             
        self.heading = start_heading  
        self.visited = {(0, 0)}
        self.known_walls = set()
        self.last_action = None

    def sense_and_act(self, percept: dict) -> str:
       
       
       
        if self.last_action == 'move_forward':
            dx, dy = DIRECTIONS[self.heading]
            self.pos = (self.pos[0] + dx, self.pos[1] + dy)
        elif self.last_action == 'turn_left':
            self.heading = (self.heading - 1) % 4
        elif self.last_action == 'turn_right':
            self.heading = (self.heading + 1) % 4
        self.visited.add(self.pos)

       
        fx, fy = DIRECTIONS[self.heading]
        forward_cell = (self.pos[0] + fx, self.pos[1] + fy)
        if percept['wall_ahead']:
            self.known_walls.add(forward_cell)

       
        action = self._decide(percept, forward_cell)
        self.last_action = action
        return action

    def _fresh(self, cell):
        """A cell worth going to: not visited and not a known wall."""
        return cell not in self.visited and cell not in self.known_walls

    def _decide(self, percept, forward_cell):
        if percept['food_here']:
            return 'suck'

        lx, ly = DIRECTIONS[(self.heading - 1) % 4]
        rx, ry = DIRECTIONS[(self.heading + 1) % 4]
        left_cell = (self.pos[0] + lx, self.pos[1] + ly)
        right_cell = (self.pos[0] + rx, self.pos[1] + ry)

        
        if not percept['wall_ahead'] and self._fresh(forward_cell):
            return 'move_forward'
        
        if self._fresh(left_cell):
            return 'turn_left'
        if self._fresh(right_cell):
            return 'turn_right'
        
        if not percept['wall_ahead']:
            return 'move_forward'
        return 'turn_left'


class GridGameGUI:
    """Tkinter wrapper. Now driven by an agent's sense_and_act() instead of random moves."""

    def __init__(self, root, agent, width=10, height=10, num_food=12,
                 num_opponents=2, walls=None, max_steps=60):
        self.root = root
        self.root.title("IT3012 - Scalable Multi-Agent Grid Hunt")
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
        cx = ax * self.cell_size + self.cell_size / 2
        cy = (self.env.height - 1 - ay) * self.cell_size + self.cell_size / 2
        hdx, hdy = DIRECTIONS[self.env.heading]
        self.canvas.create_line(cx, cy, cx + hdx * self.cell_size * 0.4,
                                cy - hdy * self.cell_size * 0.4,   # minus: screen y is flipped
                                fill="white", width=3)

    def run_loop(self):
        self.btn.config(state="disabled")

        def step():
            if not self.env.is_done():
                percept = self.env.get_percept()
                action = self.agent.sense_and_act(percept)     
                self.env.execute_action(action)
                self.draw_grid()
                self.label.config(
                    text=f"Score: {self.env.score} | Steps: {self.env.steps} | "
                         f"Facing: {DIR_NAMES[self.env.heading]} | Action: {action}")
                self.root.after(200, step)
            else:
                end = (f"Collision! Game Over! Final Score: {self.env.score}"
                       if self.env.collision else f"Finished! Final Score: {self.env.score}")
                self.label.config(text=end)
                self.btn.config(state="normal")

        step()


if __name__ == "__main__":
   
    AGENT_TYPE = "model"

    agent = SimpleReflexAgent() if AGENT_TYPE == "reflex" else ModelBasedAgent(start_heading=0)

    root = tk.Tk()
    app = GridGameGUI(root, agent=agent, width=12, height=12, num_food=15,
                      num_opponents=0, max_steps=200)
    root.mainloop()
