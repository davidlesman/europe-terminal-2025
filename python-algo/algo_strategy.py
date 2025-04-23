import gamelib
import random
import math
import warnings
from sys import maxsize
import json

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
        # Build line of walls
        wall_pos = [[i, 13] for i in range(28)]
        del wall_pos[13:15]  # make hole middle
        game_state.attempt_spawn(WALL, wall_pos)

        # Add support two rows below
        support_pos = [[11, 12], [16, 12]]
        game_state.attempt_spawn(SUPPORT, support_pos)

        # Add main turrets
        main_turret_pos = [[12, 12], [15, 12], [12, 10], [15, 10]]
        game_state.attempt_spawn(TURRET, main_turret_pos)

        if game_state.turn_number >= 3:
            # Add supports, turrets
            support_pos.extend([[10, 12], [17, 12]])
            game_state.attempt_spawn(SUPPORT, support_pos)

            lower_turret_pos = [[11, 8], [17, 8], [9, 5], [18, 5]]
            game_state.attempt_spawn(TURRET, lower_turret_pos)

        if game_state.turn_number >= 6:
            # start upgrades, more turrets
            game_state.attempt_upgrade(main_turret_pos)

            sub_turret_pos = [[3, 11], [7, 11], [20, 11], [24, 11]]
            game_state.attempt_spawn(TURRET, sub_turret_pos)

    def offense(self, game_state):
        """Interceptors every round (I).
        Interchange demolishers and scouts (DS).
        Interchange position of I and DS every round."""
        ldiagonal = [
            [0, 13],
            [1, 12],
            [2, 11],
            [3, 10],
            [4, 9],
            [5, 8],
            [6, 7],
            [7, 6],
            [8, 5],
            [9, 4],
            [10, 3],
            [11, 2],
            [12, 1],
            [13, 0],
        ]
        rdiagonal = [[i + 14, i] for i in range(14)]
        ldiagonal.extend(rdiagonal)

        # Interchange scouts and demolishers
        if random.randint(0, 1):
            spawn_positions = []
            for i in range(6):
                spawn_positions.append(random.choice(ldiagonal))
            game_state.attempt_spawn(SCOUT, spawn_positions)
        else:
            spawn_positions = []
            for i in range(2):
                spawn_positions.append(random.choice(ldiagonal))
            game_state.attempt_spawn(DEMOLISHER, spawn_positions)

        # Interceptor
        spawn_positions = []
        for i in range(2):
            spawn_positions.append(random.choice(ldiagonal))
        game_state.attempt_spawn(INTERCEPTOR, spawn_positions)


if __name__ == "__main__":
    algo = AlgoStrategy()
    algo.start()
