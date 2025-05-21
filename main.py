from model import AntColonyModel
from visualization import create_server

# Simulation parameters
WIDTH = 150
HEIGHT = 150
CANVAS_WIDTH = 800
CANVAS_HEIGHT = 800

# Sets up and runs the ant colony simulation
# Input:
#   - None
# Output:
#   - None (launches the simulation server)
def run_simulation():
    # Create visualization server
    server = create_server(
        AntColonyModel, 
        width=WIDTH, 
        height=HEIGHT, 
        canvas_width=CANVAS_WIDTH, 
        canvas_height=CANVAS_HEIGHT
    )
    
    # Configure and launch the server
    server.port = 8521  # The default
    server.launch()

# Run the simulation when executed directly
if __name__ == "__main__":
    run_simulation() 