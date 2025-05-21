from mesa import Agent
import numpy as np

# =====================================================
# AntAgent: An ant agent that searches for food and returns it to the nest
#
# This implementation uses a two-pheromone system:
# - "to_nest" pheromones: Laid by ants carrying food back to the nest
# - "to_food" pheromones: Laid by ants returning to a known food source
#
# This dual-pheromone system creates bidirectional trails that help ants
# both find food sources and return to the nest efficiently.
# =====================================================
class AntAgent(Agent):
    
    # Constructor
    # Input:
    #   - unique_id: Unique identifier for the agent
    #   - model: The model containing the agent
    # Output:
    #   - Initialized AntAgent
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.carrying_food = False
        self.direction = np.random.randint(8)  # Direction represented as integers 0-7
        self.home_pos = self.model.nest_pos
        self.last_direction = None  # Remember last movement direction for momentum
        self.detection_radius = 2  # Increased detection radius for pheromones
        
        # Add food source memory
        self.last_food_pos = None  # Remember where food was found
        self.returning_to_food = False  # Whether currently trying to return to food source
        
        # For analytics
        self.following_pheromones = False
        self.just_dropped_food = False  # To track if ant just returned with food
        self.exploration_cooldown = 0  # Counter to force exploration after dropping food
    
    # Main movement function that determines where the ant should move next
    # Input:
    #   - None (uses self.pos and model state)
    # Output:
    #   - next_pos: The position that the ant moved to
    def move(self):
        # Get the current position
        current_pos = self.pos
        possible_steps = self.model.grid.get_neighborhood(
            current_pos, 
            moore=True,  # Use Moore neighborhood (8 surrounding cells)
            include_center=False
        )
        
        # If ant just dropped food, it should move away from the nest to avoid clustering
        if self.just_dropped_food or self.exploration_cooldown > 0:
            next_pos = self.move_away_from_nest(current_pos, possible_steps)
            self.just_dropped_food = False
            self.exploration_cooldown = max(0, self.exploration_cooldown - 1)
            self.following_pheromones = False
            
            # Drop "to_food" pheromone when moving away from nest after delivering food
            if self.returning_to_food and self.last_food_pos:
                self.model.create_pheromone(current_pos, strength=1.0, pheromone_type="to_food")
                
        elif self.carrying_food:
            # If carrying food, head back to nest
            next_pos = self.move_towards(current_pos, self.home_pos)
            
            # Drop stronger "to_nest" pheromone when carrying food, but not too close to nest
            nest_x, nest_y = self.home_pos
            pos_x, pos_y = current_pos
            dist_to_nest = ((pos_x - nest_x) ** 2 + (pos_y - nest_y) ** 2) ** 0.5
            if dist_to_nest > 3:  # Don't drop pheromones very close to nest
                self.model.create_pheromone(current_pos, strength=1.5, pheromone_type="to_nest")
            
            self.following_pheromones = False
            
        elif self.returning_to_food and self.last_food_pos:
            # If trying to return to a known food source
            if self.pos == self.last_food_pos:
                # We've arrived at the last food position
                self.returning_to_food = False
                # Look for food at this location
                # Use an immediate random step since we'll look for food in the step method
                next_pos = self.random.choice(possible_steps)
                self.following_pheromones = False
            else:
                # Move toward the remembered food position
                next_pos = self.move_towards(current_pos, self.last_food_pos)
                # Drop "to_food" pheromone while returning to a known food source
                self.model.create_pheromone(current_pos, strength=1.0, pheromone_type="to_food")
                self.following_pheromones = False
                
        else:
            # Not carrying food - look for food or follow pheromones
            # First check for food in nearby cells (expanded radius)
            food_cells = []
            # Check immediate neighborhood for food
            nearby_cells = self.model.grid.get_neighborhood(
                current_pos, moore=True, include_center=False, radius=2
            )
            
            for cell in nearby_cells:
                cell_contents = self.model.grid.get_cell_list_contents([cell])
                for agent in cell_contents:
                    if isinstance(agent, FoodAgent):
                        # If it's in immediate neighborhood, prioritize it
                        if cell in possible_steps:
                            food_cells.append(cell)
                        # Otherwise, move in that general direction
                        elif len(food_cells) == 0:
                            # Find a step in the general direction of food
                            for step in possible_steps:
                                step_x, step_y = step
                                food_x, food_y = cell
                                # If step is in the direction of food
                                if (step_x - current_pos[0]) * (food_x - current_pos[0]) >= 0 and \
                                   (step_y - current_pos[1]) * (food_y - current_pos[1]) >= 0:
                                    food_cells.append(step)
            
            if food_cells:
                # Move to a cell with food or toward food
                next_pos = self.random.choice(food_cells)
                self.following_pheromones = False
            else:
                # No food nearby, follow pheromones or do random walk
                # Check if we're near the nest - prioritize moving away if yes
                nest_x, nest_y = self.home_pos
                pos_x, pos_y = current_pos
                dist_to_nest = ((pos_x - nest_x) ** 2 + (pos_y - nest_y) ** 2) ** 0.5
                
                if dist_to_nest < 5 and self.random.random() < 0.8:
                    # Near nest - move away to avoid clustering
                    next_pos = self.move_away_from_nest(current_pos, possible_steps)
                    self.following_pheromones = False
                else:
                    # Follow pheromones or explore
                    next_pos, is_following = self.follow_pheromones_or_explore(current_pos, possible_steps)
                    self.following_pheromones = is_following
        
        # Store the movement direction for next time
        if self.last_direction:
            dx = next_pos[0] - current_pos[0]
            dy = next_pos[1] - current_pos[1]
            self.last_direction = (dx, dy)
        else:
            self.last_direction = (0, 0)
            
        # Move to the selected position
        self.model.grid.move_agent(self, next_pos)
        return next_pos
    
    # Makes the ant move in a direction away from the nest to prevent clustering
    # Input:
    #   - current_pos: The current position of the ant
    #   - possible_steps: List of possible neighboring positions to move to
    # Output:
    #   - best_pos: The selected position to move to
    def move_away_from_nest(self, current_pos, possible_steps):
        nest_x, nest_y = self.home_pos
        pos_x, pos_y = current_pos
        
        # Calculate vector away from nest
        dx = pos_x - nest_x
        dy = pos_y - nest_y
        
        # Normalize to a unit vector
        magnitude = max(0.1, (dx**2 + dy**2)**0.5)  # Avoid division by zero
        dx /= magnitude
        dy /= magnitude
        
        # Scale to reach a good exploration distance
        target_x = int(pos_x + dx * 10) % self.model.width
        target_y = int(pos_y + dy * 10) % self.model.height
        
        # Find step in the direction away from nest
        best_pos = None
        min_dist_to_nest = float('inf')
        
        for pos in possible_steps:
            dist_to_nest = ((pos[0] - nest_x)**2 + (pos[1] - nest_y)**2)**0.5
            if dist_to_nest > min_dist_to_nest:
                min_dist_to_nest = dist_to_nest
                best_pos = pos
        
        if best_pos:
            return best_pos
        
        # Fallback to random walk if no good direction found
        return self.random.choice(possible_steps)
    
    # Looks for pheromones in a wider area and follows them, or explores randomly
    # Input:
    #   - current_pos: The current position of the ant
    #   - possible_steps: List of possible neighboring positions to move to
    # Output:
    #   - next_position: The selected position to move to
    #   - is_following: Boolean indicating if following pheromones (True) or random walk (False)
    def follow_pheromones_or_explore(self, current_pos, possible_steps):
        # Check all cells within detection radius for pheromones
        max_pheromone = 0
        best_direction = None
        pheromone_type_to_follow = "to_food"  # When not carrying food, look for food trails
        
        # Get all cells in the wider detection radius
        wider_neighborhood = self.model.grid.get_neighborhood(
            current_pos, moore=True, include_center=False, radius=self.detection_radius
        )
        
        # Calculate pheromone strength and direction for each cell
        pheromone_directions = {}
        for pos in wider_neighborhood:
            cell_contents = self.model.grid.get_cell_list_contents([pos])
            pheromone_strength = 0
            
            # We follow to_food pheromones when looking for food
            for agent in cell_contents:
                if isinstance(agent, PheromoneAgent):
                    if agent.pheromone_type == pheromone_type_to_follow:
                        pheromone_strength += agent.strength * 1.5  # Higher weight for correct type
            
            if pheromone_strength > 0.1:  # Lowered threshold for detection
                # Calculate direction to this cell
                dx = pos[0] - current_pos[0]
                dy = pos[1] - current_pos[1]
                direction = (dx, dy)
                
                # Store or update direction strength
                if direction in pheromone_directions:
                    pheromone_directions[direction] += pheromone_strength
                else:
                    pheromone_directions[direction] = pheromone_strength
                
                # Keep track of strongest direction
                if pheromone_directions[direction] > max_pheromone:
                    max_pheromone = pheromone_directions[direction]
                    best_direction = direction
        
        # Choose a step based on pheromone information or random walk
        if best_direction and self.random.random() < min(0.95, 0.6 + max_pheromone * 0.3):
            # Try to move in the direction of strongest pheromone
            dx, dy = best_direction
            # Normalize to get a single step
            if abs(dx) > 1 or abs(dy) > 1:
                dx = 1 if dx > 0 else (-1 if dx < 0 else 0)
                dy = 1 if dy > 0 else (-1 if dy < 0 else 0)
            
            target_pos = ((current_pos[0] + dx) % self.model.width, 
                          (current_pos[1] + dy) % self.model.height)
            
            # If this position is in our possible steps, move there
            if target_pos in possible_steps:
                return target_pos, True
            else:
                # Find the closest available step to the target direction
                min_angle_diff = float('inf')
                best_step = None
                
                for step in possible_steps:
                    step_dx = step[0] - current_pos[0]
                    step_dy = step[1] - current_pos[1]
                    
                    # Calculate angular difference
                    target_angle = np.arctan2(dy, dx)
                    step_angle = np.arctan2(step_dy, step_dx)
                    angle_diff = abs(target_angle - step_angle)
                    angle_diff = min(angle_diff, 2 * np.pi - angle_diff)  # Handle circular difference
                    
                    if angle_diff < min_angle_diff:
                        min_angle_diff = angle_diff
                        best_step = step
                
                if best_step:
                    return best_step, True
        
        # Fall back to random walk with momentum
        return self.random_walk(possible_steps), False
    
    # Performs a random walk with some directional momentum
    # Input:
    #   - possible_steps: List of possible neighboring positions to move to
    # Output:
    #   - selected_position: The chosen position to move to
    def random_walk(self, possible_steps):
        if self.last_direction and self.random.random() < 0.3:
            # Try to continue in same general direction
            current_x, current_y = self.pos
            dx, dy = self.last_direction
            preferred_pos = (current_x + dx, current_y + dy)
            
            # Check if the preferred position is in possible steps
            if preferred_pos in possible_steps:
                return preferred_pos
        
        # Fall back to completely random
        return self.random.choice(possible_steps)
    
    # Moves towards a target position within the grid
    # Input:
    #   - current: Current position
    #   - target: Target position to move towards
    # Output:
    #   - best_pos: The position that moves closest to the target
    def move_towards(self, current, target):
        possible_steps = self.model.grid.get_neighborhood(
            current, moore=True, include_center=False
        )
        
        # Find cell closest to target
        min_dist = float('inf')
        best_pos = None
        
        for pos in possible_steps:
            dist = ((pos[0] - target[0]) ** 2 + (pos[1] - target[1]) ** 2) ** 0.5
            if dist < min_dist:
                min_dist = dist
                best_pos = pos
                
        return best_pos
    
    # Tries to pick up food at the current location
    # Input:
    #   - None (uses self.pos)
    # Output:
    #   - Boolean: True if food was picked up, False otherwise
    def pick_up_food(self):
        if not self.carrying_food:
            cell_contents = self.model.grid.get_cell_list_contents([self.pos])
            for agent in cell_contents:
                if isinstance(agent, FoodAgent):
                    self.carrying_food = True
                    self.last_food_pos = self.pos  # Remember where food was found
                    self.model.grid.remove_agent(agent)
                    self.model.schedule.remove(agent)
                    return True
        return False
    
    # Drops food at the nest if carrying and at nest location
    # Input:
    #   - None (uses self.pos and self.carrying_food)
    # Output:
    #   - Boolean: True if food was dropped, False otherwise
    def drop_food_at_nest(self):
        if self.carrying_food:
            x, y = self.pos
            nest_x, nest_y = self.home_pos
            # Check if at or adjacent to nest
            if abs(x - nest_x) <= 1 and abs(y - nest_y) <= 1:
                self.carrying_food = False
                self.model.food_delivered += 1
                
                # Set flags for after dropping food
                self.just_dropped_food = True
                self.returning_to_food = True  # Try to return to last food location
                self.exploration_cooldown = 5  # Force exploration for next 5 steps
                
                return True
        return False
    
    # Main step function for the ant agent
    # Input:
    #   - None
    # Output:
    #   - None
    def step(self):
        # First check if we're at food and not carrying
        if not self.carrying_food:
            self.pick_up_food()
            
        # Then move
        self.move()
        
        # If carrying food and at nest, drop it
        if self.carrying_food:
            self.drop_food_at_nest()


# =====================================================
# NestAgent: The central hub for the ant colony
# =====================================================
class NestAgent(Agent):
    
    # Constructor
    # Input:
    #   - unique_id: Unique identifier for the agent
    #   - model: The model containing the agent
    # Output:
    #   - Initialized NestAgent
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.food_stored = 0
    
    # Main step function for the nest agent
    # Input:
    #   - None
    # Output:
    #   - None
    def step(self):
        # The nest doesn't move but can perform colony-level coordination
        # For example, it could adjust foraging strategies based on food levels
        pass


# =====================================================
# FoodAgent: Represents a food resource in the environment
# =====================================================
class FoodAgent(Agent):
    
    # Constructor
    # Input:
    #   - unique_id: Unique identifier for the agent
    #   - model: The model containing the agent
    #   - amount: Amount of food units (default 1)
    # Output:
    #   - Initialized FoodAgent
    def __init__(self, unique_id, model, amount=1):
        super().__init__(unique_id, model)
        self.amount = amount
    
    # Main step function for the food agent
    # Input:
    #   - None
    # Output:
    #   - None
    def step(self):
        # Food doesn't do anything on its own
        pass


# =====================================================
# PheromoneAgent: Represents a pheromone trail left by ants
# =====================================================
class PheromoneAgent(Agent):
    
    # Constructor
    # Input:
    #   - unique_id: Unique identifier for the agent
    #   - model: The model containing the agent
    #   - strength: Initial pheromone strength
    #   - pheromone_type: Type of pheromone ("to_nest" or "to_food")
    # Output:
    #   - Initialized PheromoneAgent
    def __init__(self, unique_id, model, strength=1.0, pheromone_type="to_nest"):
        super().__init__(unique_id, model)
        self.strength = strength
        self.pheromone_type = pheromone_type  # "to_nest" or "to_food"
    
    # Main step function for the pheromone agent
    # Input:
    #   - None
    # Output:
    #   - None
    def step(self):
        # Use specific evaporation rate depending on pheromone type
        if self.pheromone_type == "to_nest":
            self.strength *= self.model.to_nest_evaporation
        else:  # "to_food"
            self.strength *= self.model.to_food_evaporation
        
        # Remove pheromone if it's too weak
        if self.strength < 0.05:
            self.model.grid.remove_agent(self)
            self.model.schedule.remove(self) 