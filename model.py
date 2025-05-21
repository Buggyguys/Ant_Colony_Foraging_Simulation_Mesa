from mesa import Model
from mesa.space import MultiGrid
from mesa.time import RandomActivation
from mesa.datacollection import DataCollector
import numpy as np
import csv
import os
from datetime import datetime
from agents import AntAgent, NestAgent, FoodAgent, PheromoneAgent

# =====================================================
# AntColonyModel: Main model for simulating ant colony foraging behavior
#
# This model implements a sophisticated dual-pheromone system:
# - "to_nest" pheromones - guide ants from food sources back to the nest
# - "to_food" pheromones - guide ants from the nest to food sources
#
# The model allows configuring separate evaporation rates for each pheromone type,
# which controls how long trails persist in the environment.
# =====================================================
class AntColonyModel(Model):
    
    # Constructor - initializes the simulation environment
    # Input:
    #   - width, height: Dimensions of the grid
    #   - n_ants: Number of ant agents
    #   - n_food_piles: Number of food piles in the environment
    #   - food_pile_size: Amount of food in each pile
    #   - simulation_speed: Speed multiplier for the simulation
    #   - to_nest_lifespan: Lifespan of to-nest pheromones in seconds
    #   - to_food_lifespan: Lifespan of to-food pheromones in seconds
    #   - save_data: Whether to save simulation data to CSV
    # Output:
    #   - Initialized AntColonyModel
    def __init__(self, width=100, height=100, n_ants=50, n_food_piles=5, food_pile_size=100, simulation_speed=1, to_nest_lifespan=10, to_food_lifespan=6, save_data=False):
        super().__init__()
        self.width = width
        self.height = height
        self.n_ants = n_ants
        self.schedule = RandomActivation(self)
        self.grid = MultiGrid(width, height, torus=True)
        self.simulation_speed = simulation_speed
        
        # Pheromone lifespans in seconds and derived evaporation rates
        self.to_nest_lifespan = to_nest_lifespan
        self.to_food_lifespan = to_food_lifespan
        
        # Convert lifespans to evaporation rates
        # We assume 10 steps per second as the base rate
        self.steps_per_second = 10
        self.to_nest_evaporation = self._lifespan_to_evaporation(to_nest_lifespan)
        self.to_food_evaporation = self._lifespan_to_evaporation(to_food_lifespan)
        
        # Initialize model state
        self.food_delivered = 0
        self.total_food = 0
        self.step_count = 0
        self.active_pheromones = 0
        self.active_to_nest_pheromones = 0
        self.active_to_food_pheromones = 0
        self.next_id_value = 0  # For generating unique IDs
        
        # Stats for analysis
        self.ants_at_nest = 0
        self.ants_following_pheromones = 0
        self.ants_random_walking = 0
        
        # For saving data (disabled by default for better performance)
        self.data_collection_interval = 10  # Steps between data collection
        self.save_data = save_data
        
        # Only initialize file if data saving is enabled
        if self.save_data:
            # Generate a unique timestamp for the filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.data_filename = f"ant_colony_data_{timestamp}.csv"
            
            # Write header to CSV
            with open(self.data_filename, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow([
                    'Step', 'Food_Delivered', 'Active_Pheromones', 'To_Nest_Pheromones', 'To_Food_Pheromones',
                    'Ants_With_Food', 'Ants_At_Nest', 'Ants_Following_Pheromones',
                    'Ants_Random_Walking', 'Food_Efficiency'
                ])
        
        # Place nest in the center
        self.nest_pos = (width//2, height//2)
        nest = NestAgent(self.next_id(), self)
        self.grid.place_agent(nest, self.nest_pos)
        self.schedule.add(nest)
        
        # Create and place ant agents
        for i in range(self.n_ants):
            ant = AntAgent(self.next_id(), self)
            # Place ants around the nest in a cluster
            x = self.nest_pos[0] + self.random.randint(-5, 5)
            y = self.nest_pos[1] + self.random.randint(-5, 5)
            pos = (x % self.width, y % self.height)  # Ensure within grid bounds
            self.grid.place_agent(ant, pos)
            self.schedule.add(ant)
        
        # Place food piles
        self.place_food(n_food_piles, food_pile_size)
        
        # Initialize DataCollector
        self.datacollector = DataCollector(
            model_reporters={
                "Food Delivered": lambda m: m.food_delivered,
                "Active Pheromones": lambda m: m.active_pheromones,
                "To Nest Pheromones": lambda m: m.active_to_nest_pheromones,
                "To Food Pheromones": lambda m: m.active_to_food_pheromones,
                "Ants With Food": lambda m: sum(1 for a in m.schedule.agents 
                                              if isinstance(a, AntAgent) and a.carrying_food),
                "Food Efficiency": lambda m: m.food_delivered / (m.step_count + 1) if m.step_count > 0 else 0
            },
            agent_reporters={"Carrying Food": lambda a: getattr(a, "carrying_food", None)}
        )
        
        # Print debug info about pheromone settings
        self._print_pheromone_details()
    
    # Generates unique sequential IDs for agents
    # Input:
    #   - None
    # Output:
    #   - unique_id: The next unique ID
    def next_id(self):
        self.next_id_value += 1
        return self.next_id_value
    
    # Places food piles in the environment at random locations
    # Input:
    #   - n_piles: Number of food piles to create
    #   - pile_size: Amount of food per pile
    # Output:
    #   - None (modifies model state)
    def place_food(self, n_piles, pile_size):
        min_dist = max(self.width, self.height) // 8  # Minimum distance from nest scales with grid size
        
        for _ in range(n_piles):
            while True:
                x = self.random.randrange(self.grid.width)
                y = self.random.randrange(self.grid.height)
                # Calculate distance from nest
                nest_x, nest_y = self.nest_pos
                dist = ((x - nest_x) ** 2 + (y - nest_y) ** 2) ** 0.5
                if dist > min_dist:
                    break
            
            # Create a circular food pile
            food_per_cell = pile_size // 20  # Distribute food over cells
            for dx in range(-2, 3):
                for dy in range(-2, 3):
                    if dx*dx + dy*dy <= 4:  # Radius of 2
                        food_x = int(min(max(x + dx, 0), self.width-1))
                        food_y = int(min(max(y + dy, 0), self.height-1))
                        # Create food agents at this position
                        for _ in range(food_per_cell):
                            food = FoodAgent(self.next_id(), self)
                            self.grid.place_agent(food, (food_x, food_y))
                            self.schedule.add(food)
                            self.total_food += 1
    
    # Creates a pheromone agent at the specified position and in adjacent cells
    # Input:
    #   - pos: Position to create the pheromone
    #   - strength: Initial pheromone strength
    #   - pheromone_type: Type of pheromone ("to_nest" or "to_food")
    # Output:
    #   - None (modifies model state)
    def create_pheromone(self, pos, strength=1.0, pheromone_type="to_nest"):
        # Check if we're near the nest - reduce pheromone strength near nest to prevent clustering
        nest_x, nest_y = self.nest_pos
        pos_x, pos_y = pos
        dist_to_nest = ((pos_x - nest_x) ** 2 + (pos_y - nest_y) ** 2) ** 0.5
        
        # Reduce pheromone strength closer to the nest to prevent clustering
        if dist_to_nest < 10:
            # Gradually reduce strength as we get closer to nest
            strength *= (dist_to_nest / 10) 
            
            # Very close to nest, no need for strong pheromones at all
            if dist_to_nest < 3:
                return
        
        # Create pheromone at the current position with full strength
        self._add_or_reinforce_pheromone(pos, strength, pheromone_type)
        
        # Create weaker pheromones in adjacent cells to make trails wider and easier to follow
        neighborhood = self.grid.get_neighborhood(pos, moore=True, include_center=False, radius=1)
        for neighbor_pos in neighborhood:
            # Add weaker pheromone to neighboring cells (30% of original strength)
            self._add_or_reinforce_pheromone(neighbor_pos, strength * 0.3, pheromone_type)
    
    # Helper method to add a new pheromone or reinforce an existing one
    # Input:
    #   - pos: Position for the pheromone
    #   - strength: Pheromone strength
    #   - pheromone_type: Type of pheromone ("to_nest" or "to_food")
    # Output:
    #   - None (modifies model state)
    def _add_or_reinforce_pheromone(self, pos, strength, pheromone_type):
        # Check if there's already a pheromone at this position
        cell_contents = self.grid.get_cell_list_contents([pos])
        for agent in cell_contents:
            if isinstance(agent, PheromoneAgent) and agent.pheromone_type == pheromone_type:
                # Reinforce existing pheromone of the same type
                agent.strength = min(3.0, agent.strength + strength * 0.5)
                return
        
        # Only create a new pheromone if strength is significant
        if strength >= 0.2:
            # Create new pheromone
            pheromone = PheromoneAgent(self.next_id(), self, strength=strength, pheromone_type=pheromone_type)
            self.grid.place_agent(pheromone, pos)
            self.schedule.add(pheromone)
            self.active_pheromones += 1
    
    # Removes a pheromone from the simulation
    # Input:
    #   - pheromone: The pheromone agent to remove
    # Output:
    #   - None (modifies model state)
    def remove_pheromone(self, pheromone):
        self.grid.remove_agent(pheromone)
        self.schedule.remove(pheromone)
        self.active_pheromones -= 1
        
        # Also decrement the specific type counter
        if pheromone.pheromone_type == "to_nest":
            self.active_to_nest_pheromones -= 1
        elif pheromone.pheromone_type == "to_food":
            self.active_to_food_pheromones -= 1
    
    # Collects statistics about ant behavior for analysis
    # Input:
    #   - None
    # Output:
    #   - None (updates model state with statistics)
    def collect_statistics(self):
        self.ants_with_food = 0
        self.ants_at_nest = 0
        self.ants_following_pheromones = 0
        self.ants_random_walking = 0
        
        for agent in self.schedule.agents:
            if isinstance(agent, AntAgent):
                # Count ants with food
                if agent.carrying_food:
                    self.ants_with_food += 1
                
                # Count ants near nest
                pos_x, pos_y = agent.pos
                nest_x, nest_y = self.nest_pos
                dist_to_nest = ((pos_x - nest_x) ** 2 + (pos_y - nest_y) ** 2) ** 0.5
                if dist_to_nest < 5:
                    self.ants_at_nest += 1
                
                # Count ants following pheromones vs random walking
                if hasattr(agent, 'following_pheromones'):
                    if agent.following_pheromones:
                        self.ants_following_pheromones += 1
                    else:
                        self.ants_random_walking += 1
    
    # Saves the current simulation state to CSV
    # Input:
    #   - None
    # Output:
    #   - None (writes to CSV file)
    def save_simulation_data(self):
        if not self.save_data or self.step_count % self.data_collection_interval != 0:
            return
            
        with open(self.data_filename, 'a', newline='') as csvfile:
            writer = csv.writer(csvfile)
            # Calculate metrics
            ants_with_food = sum(1 for a in self.schedule.agents 
                              if isinstance(a, AntAgent) and a.carrying_food)
            food_efficiency = self.food_delivered / (self.step_count + 1) if self.step_count > 0 else 0
            
            writer.writerow([
                self.step_count,
                self.food_delivered, 
                self.active_pheromones,
                self.active_to_nest_pheromones,
                self.active_to_food_pheromones,
                ants_with_food,
                self.ants_at_nest,
                self.ants_following_pheromones,
                self.ants_random_walking,
                food_efficiency
            ])
    
    # Converts a lifespan in seconds to an evaporation rate
    # Input:
    #   - lifespan_seconds: Desired lifespan in seconds
    # Output:
    #   - evaporation_rate: Calculated per-step evaporation rate
    def _lifespan_to_evaporation(self, lifespan_seconds):
        # Calculate how many steps the pheromone should last based on simulation speed
        # A higher simulation speed means fewer real steps to get the same perceived time
        total_steps = lifespan_seconds * self.steps_per_second / self.simulation_speed
        
        # Calculate the per-step evaporation rate
        # If we want to reach 0.05 of original strength after total_steps steps
        if total_steps <= 0:
            return 0.0  # Immediate evaporation
        
        # Calculate the per-step evaporation rate
        # If we want to reach 0.05 of original strength after total_steps steps
        evaporation_rate = (0.05) ** (1.0 / total_steps)
        
        # Make sure the rate is between 0 and 1
        return max(0.01, min(0.999, evaporation_rate))
    
    # Prints detailed information about pheromone settings (for debugging)
    # Input:
    #   - None
    # Output:
    #   - None (prints to console)
    def _print_pheromone_details(self):
        to_nest_rate = self.to_nest_evaporation
        to_food_rate = self.to_food_evaporation
        
        # Calculate how many steps until pheromone reaches threshold
        to_nest_steps = int(np.log(0.05) / np.log(to_nest_rate)) if to_nest_rate > 0 else 0
        to_food_steps = int(np.log(0.05) / np.log(to_food_rate)) if to_food_rate > 0 else 0
        
        # Calculate real-time seconds
        nest_seconds = to_nest_steps / (self.steps_per_second * self.simulation_speed)
        food_seconds = to_food_steps / (self.steps_per_second * self.simulation_speed)
        
        print(f"Pheromone Details:")
        print(f"  Simulation Speed: {self.simulation_speed}x")
        print(f"  To-Nest Pheromones:")
        print(f"    Target Lifespan: {self.to_nest_lifespan} seconds")
        print(f"    Evaporation Rate: {to_nest_rate:.6f}")
        print(f"    Steps to Fade: {to_nest_steps}")
        print(f"    Actual Lifespan: {nest_seconds:.2f} seconds")
        print(f"  To-Food Pheromones:")
        print(f"    Target Lifespan: {self.to_food_lifespan} seconds")
        print(f"    Evaporation Rate: {to_food_rate:.6f}")
        print(f"    Steps to Fade: {to_food_steps}")
        print(f"    Actual Lifespan: {food_seconds:.2f} seconds")
    
    # Main step function to advance the model by one time step
    # Input:
    #   - None
    # Output:
    #   - None (advances simulation)
    def step(self):
        # Count active pheromones before the step
        self.active_pheromones = 0
        self.active_to_nest_pheromones = 0
        self.active_to_food_pheromones = 0
        
        for agent in self.schedule.agents:
            if isinstance(agent, PheromoneAgent):
                self.active_pheromones += 1
                if agent.pheromone_type == "to_nest":
                    self.active_to_nest_pheromones += 1
                elif agent.pheromone_type == "to_food":
                    self.active_to_food_pheromones += 1
        
        # Update evaporation rates if simulation speed has changed
        # This would happen if the user adjusted the speed slider in the UI
        self.to_nest_evaporation = self._lifespan_to_evaporation(self.to_nest_lifespan)
        self.to_food_evaporation = self._lifespan_to_evaporation(self.to_food_lifespan)
        
        # Run the step multiple times if speed multiplier is set
        for _ in range(self.simulation_speed):
            self.schedule.step()
            self.step_count += 1
            
        # Collect statistics
        self.collect_statistics()
        
        # Save data if needed
        self.save_simulation_data()
        
        # Update datacollector
        self.datacollector.collect(self) 