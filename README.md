# Ant Colony Foraging Simulation

This project simulates a colony of ants searching for food in a 2D environment. The simulation demonstrates emergent cooperative behavior through a sophisticated dual-pheromone communication system between ants, inspired by how real ant colonies operate.

## Overview

In this simulation, ants start at a central nest and explore the environment to find food sources. When food is found, ants create pheromone trails that other ants can follow, leading to the emergence of efficient foraging paths. The simulation demonstrates how complex collective behaviors can emerge from simple individual rules.

## Features

- **Agent-Based Modeling**: Built using the Mesa framework for agent-based modeling
- **Dual-Pheromone System**: Separate pheromone types for bidirectional trails
- **Adaptive Behavior**: Ants dynamically switch between exploration and exploitation
- **Configurable Parameters**: Adjust ant count, food distribution, pheromone lifespans, etc.
- **Real-time Visualization**: Interactive visual representation with multiple data charts
- **Data Collection**: Automatic recording of simulation statistics for analysis

## Technologies Used

- **Python 3.8+**: Core programming language
- **Mesa 0.9.0**: Agent-based modeling framework
- **Matplotlib**: Data visualization for charts
- **NumPy**: Numerical operations and calculations
- **NetworkX**: Network structure support for Mesa

## Agent Types

The simulation includes four types of agents:

### 1. Ant Agents (AntAgent)
- Start at the nest and search for food
- Can carry one unit of food at a time
- Follow pheromone trails or explore randomly
- Create pheromone trails when returning with food or returning to food sources
- Use momentum to maintain general direction during random walks
- Have configurable detection radius for sensing pheromones

### 2. Nest Agent (NestAgent)
- Central hub where ants start and return food
- Stationary agent that serves as the colony's home base
- Located at the center of the environment

### 3. Food Agents (FoodAgent)
- Represent food resources in the environment
- Distributed in circular piles throughout the grid
- Each food agent represents one unit of food that an ant can carry

### 4. Pheromone Agents (PheromoneAgent)
- Temporary markers left by ants to communicate
- Two types:
  - **To-Nest Pheromones**: Blue, left by ants carrying food back to the nest
  - **To-Food Pheromones**: Orange, left by ants returning to a known food source
- Evaporate over time at configurable rates
- Stronger pheromones are more likely to be followed

## How the Simulation Works

### Dual-Pheromone System

1. **To-Nest Pheromones** (Blue): 
   - Created by ants carrying food back to the nest
   - Help other ants find their way back to the nest
   - Typically stronger than to-food pheromones

2. **To-Food Pheromones** (Orange): 
   - Created by ants returning to a known food source
   - Help other ants find food sources
   - Create efficient bidirectional highways between food and nest

### Ant Behavior

Ants follow these basic rules:

1. **Food Search**: 
   - When not carrying food, ants look for food in nearby cells
   - If no food is visible, they follow to-food pheromones or explore randomly
   - Random walks have momentum to maintain general direction

2. **Food Return**: 
   - When carrying food, ants navigate back to the nest
   - They deposit to-nest pheromones as they move
   - Pheromone strength decreases near the nest to prevent overcrowding

3. **Food Source Memory**: 
   - Ants remember where they found food
   - After dropping food at the nest, they attempt to return to the same food source
   - They deposit to-food pheromones on their way back to food

4. **Anti-Clustering Mechanisms**:
   - Ants are programmed to move away from the nest when there's overcrowding
   - Pheromone strength is reduced near the nest
   - After dropping food, ants have an "exploration cooldown" forcing them away from the nest

### Pheromone Mechanics

- **Wider Trails**: Pheromones are deposited at the ant's position and at lower strength in adjacent cells, creating wider, more natural trails
- **Reinforcement**: Existing pheromones can be strengthened by subsequent ants
- **Evaporation**: Pheromones gradually evaporate over time, allowing trails to adapt to changing conditions
- **Lifespan Control**: Evaporation rates are calculated to achieve desired lifespans in seconds
- **Maximum Strength**: Pheromones have a maximum strength to prevent overly dominant trails

## Running the Simulation

### Requirements
- Python 3.8+
- Dependencies listed in requirements.txt

### Installation
1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On macOS/Linux
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

### Starting the Simulation
To run the simulation:
```bash
python main.py
```

This will open a web browser with the interactive simulation interface.

## Configuration Options

The simulation offers several configurable parameters through the UI:

- **Number of Ants**: Control how many ant agents participate in the simulation (10-500)
- **Number of Food Piles**: How many discrete food sources are placed in the environment (1-20)
- **Food per Pile**: How much food is in each pile (10-1000)
- **Simulation Speed**: Accelerate the simulation (1x-10x)
- **To-Nest Pheromone Lifespan**: How long these pheromones persist in seconds (1-30)
- **To-Food Pheromone Lifespan**: How long these pheromones persist in seconds (1-20)
- **Save Simulation Data**: Toggle data saving to CSV files (disabled by default for better performance)

## Data Collection and Analysis

The simulation can collect and save the following data when data saving is enabled:
- Food delivered to the nest
- Active pheromones (total, to-nest, to-food)
- Ants carrying food
- Ants at nest vs. exploring
- Ants following pheromones vs. random walking
- Food collection efficiency

This data is saved to a timestamped CSV file for later analysis and displayed in real-time charts in the UI. For better performance during long simulation runs, data saving is disabled by default but can be enabled through the UI checkbox.

## Components
- `main.py`: Entry point of the simulation
- `model.py`: Contains the main simulation model and environment
- `agents.py`: Defines the agent classes and their behaviors
- `visualization.py`: Handles the visual representation and UI elements

## Emergent Behaviors

The simulation demonstrates several emergent phenomena seen in real ant colonies:
- Formation of efficient trails between nest and food sources
- Adaptation to changing resources (depletion of food sources)
- Self-organizing traffic patterns when trails become crowded
- Collective intelligence in finding optimal routes # Ant_Colony_Foraging_Simulation_Mesa
