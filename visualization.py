from mesa.visualization.modules import CanvasGrid, ChartModule
from mesa.visualization.ModularVisualization import ModularServer
from mesa.visualization.UserParam import UserSettableParameter
from agents import AntAgent, NestAgent, FoodAgent, PheromoneAgent

# Defines how each agent type should be displayed in the visualization
# Input:
#   - agent: The agent to be portrayed
# Output:
#   - portrayal: A dictionary with visualization properties
def agent_portrayal(agent):
    if agent is None:
        return None
        
    portrayal = {"Filled": "true"}
    
    if isinstance(agent, AntAgent):
        portrayal.update({
            "Shape": "circle",
            "r": 0.8,
            "Color": "red" if agent.carrying_food else "black",
            "Layer": 3  # Top layer
        })
    elif isinstance(agent, NestAgent):
        portrayal.update({
            "Shape": "circle",
            "r": 2,
            "Color": "brown",
            "Layer": 2  # Below ants
        })
    elif isinstance(agent, FoodAgent):
        portrayal.update({
            "Shape": "rect",
            "w": 0.7,
            "h": 0.7,
            "Color": "green",
            "Layer": 1  # Below nest
        })
    elif isinstance(agent, PheromoneAgent):
        # Use alpha value based on pheromone strength
        alpha = min(0.8, agent.strength * 0.4)  # Adjusted for visibility
        
        # Different colors for different pheromone types
        if agent.pheromone_type == "to_nest":
            color = f"rgba(0, 0, 255, {alpha})"  # Blue for to_nest
        else:  # to_food
            color = f"rgba(255, 165, 0, {alpha})"  # Orange for to_food
            
        portrayal.update({
            "Shape": "rect",
            "w": 1.0,
            "h": 1.0,
            "Color": color,
            "Layer": 0  # Bottom layer
        })
    
    return portrayal

# Creates and returns the ModularServer for the Ant Colony Simulation
# Input:
#   - model_class: The model class to use
#   - width, height: Grid dimensions
#   - canvas_width, canvas_height: Canvas pixel dimensions
# Output:
#   - server: ModularServer instance ready to launch
def create_server(model_class, width=150, height=150, canvas_width=800, canvas_height=800):
    # Create a standard grid for all agents
    grid = CanvasGrid(agent_portrayal, width, height, canvas_width, canvas_height)
    
    # Chart for food delivered over time
    food_chart = ChartModule([{"Label": "Food Delivered", "Color": "green"}], 
                        data_collector_name="datacollector")
    
    # Chart for pheromone counts - combined and individual types
    pheromone_chart = ChartModule([
        {"Label": "Active Pheromones", "Color": "purple"},
        {"Label": "To Nest Pheromones", "Color": "blue"},
        {"Label": "To Food Pheromones", "Color": "orange"}
    ], data_collector_name="datacollector")
    
    # Chart for to_nest pheromones only
    to_nest_chart = ChartModule([{"Label": "To Nest Pheromones", "Color": "blue"}],
                          data_collector_name="datacollector")
    
    # Chart for to_food pheromones only
    to_food_chart = ChartModule([{"Label": "To Food Pheromones", "Color": "orange"}],
                          data_collector_name="datacollector")
    
    # Chart for ants with food
    ants_chart = ChartModule([{"Label": "Ants With Food", "Color": "red"}],
                      data_collector_name="datacollector")
    
    # Chart for foraging efficiency
    efficiency_chart = ChartModule([{"Label": "Food Efficiency", "Color": "purple"}],
                           data_collector_name="datacollector")
    
    # Define user-configurable model parameters
    model_params = {
        "width": width, 
        "height": height,
        "n_ants": UserSettableParameter("slider", "Number of Ants", 100, 10, 500, 10),
        "n_food_piles": UserSettableParameter("slider", "Number of Food Piles", 8, 1, 20, 1),
        "food_pile_size": UserSettableParameter("slider", "Food per Pile", 200, 10, 1000, 10),
        "simulation_speed": UserSettableParameter("slider", "Simulation Speed (×)", 1, 1, 10, 1),
        "to_nest_lifespan": UserSettableParameter("slider", "To-Nest Pheromone Lifespan (sec)", 10, 1, 30, 1),
        "to_food_lifespan": UserSettableParameter("slider", "To-Food Pheromone Lifespan (sec)", 6, 1, 20, 1),
        "save_data": UserSettableParameter("checkbox", "Save Simulation Data to CSV", False)
    }
    
    # Create and configure the server
    server = ModularServer(
        model_class,
        [grid, food_chart, pheromone_chart, to_nest_chart, to_food_chart, ants_chart, efficiency_chart],
        "Ant Colony Simulation",
        model_params
    )
    
    # Make simulation run faster (higher FPS)
    server.port = 8521
    return server 