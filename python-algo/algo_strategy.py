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
        self.breaches_last_turn = []
        self.scored_on_locations = []
        self.scout_attack_side = False  # 0 for left, 1 for right

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
        self.player_index = 0
        self.unit_type_to_index = {
            unit["shorthand"]: i for i, unit in enumerate(config["unitInformation"])
        }

    def on_action_frame(self, turn_string):
        self.breaches_last_turn = []
        try:
            events = json.loads(turn_string)
            for frame_event in events.get("events", {}).get("breach", []):
                if len(frame_event) >= 3:
                    x, y, player = frame_event[:3]
                    if player != self.player_index:
                        self.breaches_last_turn.append([x, y])
                        gamelib.debug_write(f"Enemy breached at {x}, {y}")
        except Exception as e:
            gamelib.debug_write(f"[ERROR] Failed to parse action frame: {e}")

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

            wall_pos = [[7, 6], [20, 6], [1, 13], [26, 13]]
            game_state.attempt_spawn(WALL, wall_pos)

            ext_pos = [[3, 12], [24, 12], [4, 9], [23, 9], [7, 11], [20, 11]]
            game_state.attempt_spawn(TURRET, ext_pos)

            support_pos = [[11, 7], [16, 7], [12, 7], [15, 7]]
            game_state.attempt_spawn(SUPPORT, support_pos)

            ext_pos = [[9, 8], [6, 12], [18, 8], [21, 12], [10, 7], [17, 7]]
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
        left_spawns = [[8, 5], [9, 4], [10, 3], [11, 2], [12, 1], [13, 0]]
        right_spawns = [[19, 5], [14, 0], [15, 1], [16, 2], [17, 3], [18, 4]]

        # Interceptors: limit to 2 per turn by default
        interceptor_pos = [[8, 5], [19, 5]]
        interceptors_spawned = 0
        for spawn in interceptor_pos:
            if interceptors_spawned >= 2:
                break
            if game_state.get_resource(MP) >= 1 and game_state.attempt_spawn(
                INTERCEPTOR, spawn
            ):
                interceptors_spawned += 1

        # Interceptor 3: dynamic floater
        float_spawn = interceptor_pos[0]  # default

        if self.breaches_last_turn:
            last_breach = self.breaches_last_turn[-1]
            gamelib.debug_write(last_breach)
            breached_side = "left" if int(last_breach[0][0]) < 14 else "right"
            float_spawn = (
                interceptor_pos[0] if breached_side == "left" else interceptor_pos[1]
            )
            gamelib.debug_write(f"Floating interceptor redirected to {breached_side}")

        game_state.attempt_spawn(INTERCEPTOR, float_spawn)

        # attack logic
        spawn_side = left_spawns if self.scout_attack_side else right_spawns

        if game_state.turn_number % 2 == 0 and game_state.turn_number % 4 != 0:
            game_state.attempt_spawn(DEMOLISHER, spawn_side, 1)
            self.scout_attack_side = not self.scout_attack_side
        if game_state.turn_number % 4 == 0:
            scout_count = min(15, 3 + (game_state.turn_number // 2))
            scout_spawn_side = left_spawns if self.scout_attack_side else right_spawns
            spawn_point = scout_spawn_side[0]  # fixed spawn point for grouped attack
            game_state.attempt_spawn(SCOUT, spawn_point, scout_count)
            gamelib.debug_write(f"Sent {scout_count} SCOUTS from {spawn_point}")
            self.scout_attack_side = not self.scout_attack_side
        else:
            gamelib.debug_write(f"Odd Turn: Holding MP for stronger wave")


if __name__ == "__main__":
    algo = AlgoStrategy()
    algo.start()
