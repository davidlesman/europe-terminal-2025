import gamelib
import random
import math
import warnings
from sys import maxsize
import json
from gamelib.navigation import ShortestPathFinder

"""
Most of the algo code you write will be in this file unless you create new
modules yourself. Start by modifying the 'on_turn' function.

Advanced strategy tips: 

  - You can analyze action frames by modifying on_action_frame function

  - The GameState.map object can be manually manipulated to create hypothetical 
  board states. Though, we recommended making a copy of the map to preserve 
  the actual current map state.
"""


class AlgoStrategy(gamelib.AlgoCore):
    def __init__(self):
        super().__init__()
        seed = random.randrange(maxsize)
        random.seed(seed)
        gamelib.debug_write("Random seed: {}".format(seed))

    def on_game_start(self, config):
        """
        Read in config and perform any initial setup here
        """
        gamelib.debug_write("Configuring your custom algo strategy...")
        self.config = config
        global WALL, SUPPORT, TURRET, SCOUT, DEMOLISHER, INTERCEPTOR, MP, SP
        WALL = config["unitInformation"][0]["shorthand"]
        SUPPORT = config["unitInformation"][1]["shorthand"]
        TURRET = config["unitInformation"][2]["shorthand"]
        SCOUT = config["unitInformation"][3]["shorthand"]
        DEMOLISHER = config["unitInformation"][4]["shorthand"]
        INTERCEPTOR = config["unitInformation"][5]["shorthand"]
        MP = 1
        SP = 0
        # This is a good place to do initial setup
        self.scored_on_locations = []

    def on_turn(self, turn_state):
        """
        This function is called every turn with the game state wrapper as
        an argument. The wrapper stores the state of the arena and has methods
        for querying its state, allocating your current resources as planned
        unit deployments, and transmitting your intended deployments to the
        game engine.
        """
        game_state = gamelib.GameState(self.config, turn_state)
        

        gamelib.debug_write(
            "Performing turn {} of your custom algo strategy".format(
                game_state.turn_number
            )
        )
        game_state.suppress_warnings(
            True
        )  # Comment or remove this line to enable warnings.
        self.defense(game_state)
        self.offense(game_state)
        game_state.submit_turn()


    def defense(self, game_state):
        # Build basic defense first
        self.basic_d(game_state)

        # Upgrades
        self.upgrades(game_state)

    def basic_d(self, game_state):
        """Turrets on edges and basic wall funnel."""
        turret_pos = [
            [1, 12],
            [2, 12],
            [3, 11],
            [3, 10],
            [25, 12],
            [26, 12],
            [24, 11],
            [24, 10],
            [7, 10],
            [20, 10],
        ]
        game_state.attempt_spawn(TURRET, turret_pos)

        wall_pos = [[0, 13], [27, 13], [4, 9], [23, 9]]
        # inner funnel diagonals
        for i in range(6, 14):
            wall_pos.append([i, 16 - i])
            wall_pos.append([i + 8, i - 3])

        game_state.attempt_spawn(WALL, wall_pos)

        if game_state.turn_number >= 1:
            # Start building outer funnel wall
            wall_pos = [[5, 8], [6, 7], [22, 8], [21, 7]]
            game_state.attempt_spawn(WALL, wall_pos)

        if game_state.turn_number >= 2:
            # Extend turrets and build two supports in middle
            support_pos = [[13, 7], [14, 7]]
            game_state.attempt_spawn(SUPPORT, support_pos)

            ext_pos = [[2, 11], [25, 11], [6, 11], [20, 11]]
            game_state.attempt_spawn(TURRET, ext_pos)

            support_pos = [[13, 6], [14, 6], [12, 6], [15, 6]]
            game_state.attempt_spawn(SUPPORT, support_pos)

            ext_pos = [[4, 10], [23, 10], [8, 9], [19, 9]]
            game_state.attempt_spawn(TURRET, ext_pos)

            ext_pos = [[3, 12], [24, 12], [4, 9], [23, 9], [7, 11], [20, 11]]
            game_state.attempt_spawn(TURRET, ext_pos)

            support_pos = [[11, 7], [16, 7]]
            game_state.attempt_spawn(SUPPORT, support_pos)

            ext_pos = [[9, 8], [6, 12], [18, 8], [21, 12]]
            game_state.attempt_spawn(TURRET, ext_pos)

    def upgrades(self, game_state):
        # Upgrade edge walls and turrets
        game_state.attempt_upgrade([[0, 13], [27, 13], [7, 10], [20, 10]])

        # Support
        game_state.attempt_upgrade([[13, 7], [14, 7]])

        # Further upgrades are tried once every 3 turns, leave 8 backup points
        if game_state.turn_number % 3 == 0:
            game_state.attempt_upgrade([[2, 11], [25, 11], [13, 6], [14, 6]])

        if game_state.turn_number % 7 == 0:
            game_state.attempt_upgrade(
                [
                    [4, 10],
                    [23, 10],
                    [8, 9],
                    [19, 9],
                    [3, 12],
                    [24, 12],
                    [4, 9],
                    [23, 9],
                    [7, 11],
                    [20, 11],
                    [11, 7],
                    [16, 7],
                ]
            )
    
    def offense(self, game_state):
            """Offense strategy:
        - Deploy interceptors every turn (default).
        - Dynamically calculate Scouts and Demolishers based on enemy structures.
        - Adapt to ensure survival, breaking through, or dealing maximum damage.
        """
        # Left and right diagonal coordinates
            ldiagonal = [
            [0, 13], [1, 12], [2, 11], [3, 10], [4, 9], [5, 8], [6, 7], [7, 6],
            [8, 5], [9, 4], [10, 3], [11, 2], [12, 1], [13, 0]
        ]
        
            rdiagonal = [[i + 14, i] for i in range(14)]

            # Default interceptors: one on each diagonal
            spawn_positions = []
            spawn_positions.append(random.choice(ldiagonal))
            spawn_positions.append(random.choice(rdiagonal))
            game_state.attempt_spawn(INTERCEPTOR, spawn_positions)

            # Determine ideal paths
            pathfinder = ShortestPathFinder()
            pathfinder.initialize_map(game_state)  # Ensure the map is initialized

            # Flatten and filter only valid (x, y) tuples
            enemy_edges_raw = game_state.game_map.get_edges()[2:]  # Bottom + Left edges
            enemy_edges = [point for edge in enemy_edges_raw for point in edge if isinstance(point, (tuple, list)) and len(point) == 2]
            ideal_path_left = pathfinder.navigate_multiple_endpoints(
                spawn_positions[0], enemy_edges, game_state
            )
            ideal_path_right = pathfinder.navigate_multiple_endpoints(
                spawn_positions[1], enemy_edges, game_state
            )

            # Analyze enemy structures along the paths
            def analyze_path(path):
                enemy_structures = []
                for location in path:
                    if game_state.game_map[location]:  # Check if there are units at the location
                        unit = game_state.game_map[location][0]
                        if unit.player_index != 0:  # Enemy structure
                            unit_config = self.config["unitInformation"][unit.unit_type]
                            enemy_structures.append({
                                "location": location,
                                "health": unit.health,
                                "type": unit.unit_type,
                                "range": unit_config.get("attackRange", 0),
                                "damage": unit_config.get("attackDamageWalker", 0)
                            })
                return enemy_structures

            if ideal_path_left:
                enemy_structures_left = analyze_path(ideal_path_left)
            if ideal_path_right:
                enemy_structures_right = analyze_path(ideal_path_right)

            # Simulate damage and decide unit deployment
            def simulate_and_deploy(path, enemy_structures):
                total_damage = sum(structure["damage"] for structure in enemy_structures)

                # Decide unit type and quantity
                if total_damage == 0:
                    # No defenses, send Scouts to score
                    game_state.attempt_spawn(SCOUT, path[0], 5)  # Deploy 5 Scouts
                else:
                    # Defenses present, calculate required units
                    total_health = sum(structure["health"] for structure in enemy_structures)
                    if total_health < 50:  # Arbitrary threshold for weak defenses
                        game_state.attempt_spawn(SCOUT, path[0], 5)  # Deploy 5 Scouts
                    else:
                        game_state.attempt_spawn(DEMOLISHER, path[0], 3)  # Deploy 3 Demolishers

            if ideal_path_left:
                # Simulate and deploy for left path
                simulate_and_deploy(ideal_path_left, enemy_structures_left)
            if ideal_path_right:
                simulate_and_deploy(ideal_path_right, enemy_structures_right)
            



if __name__ == "__main__":
    algo = AlgoStrategy()
    algo.start()
