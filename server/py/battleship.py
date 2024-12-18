from typing import List, Optional
from pydantic import BaseModel, Field
from enum import Enum
import random
from server.py.game import Game, Player


class ActionType(str, Enum):
    SET_SHIP = 'set_ship'
    SHOOT = 'shoot'


class BattleshipAction(BaseModel):
    action_type: ActionType
    ship_name: Optional[str]  # Only for SET_SHIP actions
    location: List[str]


class Ship(BaseModel):
    # Name of the ship, like "Carrier" or "Battleship"
    name: str

    # Length of the ship, must be greater than 0
    length: int = Field(..., gt=0, description="Length of the ship must be greater than 0")

    # List of grid coordinates where the ship is placed; optional and defaults to None
    location: Optional[List[str]] = Field(default=None, description="Coordinates of the ship's location")

    class Config:
        """
        Pydantic configuration for the Ship class.

        This allows mutation of attributes like `location` after the model is instantiated,
        which is useful for updating the ship's state during the game.
        """
        allow_mutation = True

class PlayerState:

    def __init__(self, name: str, ships: List[Ship], shots: List[str], successful_shots: List[str]) -> None:
        self.name = name
        self.ships = ships
        self.shots = shots
        self.successful_shots = successful_shots


class GamePhase(str, Enum):
    SETUP = 'setup'            # before the game has started (including setting ships)
    RUNNING = 'running'        # while the game is running (shooting)
    FINISHED = 'finished'      # when the game is finished


class BattleshipGameState(BaseModel):
    idx_player_active: int
    phase: GamePhase
    winner: Optional[int]
    players: List[PlayerState]


class Battleship(Game):

    def __init__(self):
        self.grid_size = 10
        # Ships using the updated Ship class
        self.ships = [
            Ship(name="Carrier", length=5, location=[]),
            Ship(name="Battleship", length=4, location=[]),
            Ship(name="Cruiser", length=3, location=[]),
            Ship(name="Submarine", length=3, location=[]),
            Ship(name="Destroyer", length=2, location=[]),
        ]
        self.state = BattleshipGameState(
            idx_player_active=0,
            phase=GamePhase.SETUP,
            winner=None,
            players=[
                PlayerState("Player 1", [], [], []),
                PlayerState("Player 2", [], [], []),
            ],
        )

    def print_state(self) -> None:
        """ Set the game to a given state """
        for player in self.state.players:
            print(f"{player.name}'s State:")
            print(f"  Ships: {[ship.name + ': ' + str(ship.location) for ship in player.ships]}")
            print(f"  Shots: {player.shots}")
            print(f"  Successful Shots: {player.successful_shots}")
        print(f"Game Phase: {self.state.phase}")
        print(f"Active Player: Player {self.state.idx_player_active + 1}")

    def get_state(self) -> BattleshipGameState:
        """ Get the complete, unmasked game state """
        return self.state

    def set_state(self, state: BattleshipGameState) -> None:
        """ Print the current game state """
        self.state = state

    def get_list_action(self) -> List[BattleshipAction]:
        """ Get a list of possible actions for the active player """
        actions = []
        active_player = self.state.players[self.state.idx_player_active]

        if self.state.phase == GamePhase.SETUP:
            if len(active_player.ships) < len(self.ships):
                ship = self.ships[len(active_player.ships)]
                for i in range(self.grid_size):
                    for j in range(self.grid_size - ship.length + 1):
                        location = [f"{chr(65 + i)}{k + 1}" for k in range(j, j + ship.length)]
                        actions.append(BattleshipAction(ActionType.SET_SHIP, ship.name, location))
        elif self.state.phase == GamePhase.RUNNING:
            for i in range(self.grid_size):
                for j in range(self.grid_size):
                    target = f"{chr(65 + i)}{j + 1}"
                    if target not in active_player.shots:
                        actions.append(BattleshipAction(ActionType.SHOOT, None, [target]))
        return actions

    def apply_action(self, action: BattleshipAction) -> None:
        """ Apply the given action to the game """
        active_player = self.state.players[self.state.idx_player_active]

        if action.action_type == ActionType.SET_SHIP:
            ship = next(s for s in self.ships if s.name == action.ship_name)
            ship.location = action.location
            active_player.ships.append(ship)

            if len(active_player.ships) == len(self.ships) and all(len(p.ships) == len(self.ships) for p in self.state.players):
                self.state.phase = GamePhase.RUNNING
        elif action.action_type == ActionType.SHOOT:
            target = action.location[0]
            active_player.shots.append(target)
            opponent = self.state.players[1 - self.state.idx_player_active]
            for ship in opponent.ships:
                if target in ship.location:
                    active_player.successful_shots.append(target)
                    ship.location.remove(target)
                    break

            if all(len(ship.location) == 0 for ship in opponent.ships):
                self.state.phase = GamePhase.FINISHED
                self.state.winner = self.state.idx_player_active

        if self.state.phase == GamePhase.RUNNING:
            self.state.idx_player_active = 1 - self.state.idx_player_active

    def get_player_view(self, idx_player: int) -> BattleshipGameState:
        """ Get the masked state for the active player (e.g. the oppontent's cards are face down)"""
        """ Get the masked state for the active player """
        state_copy = self.get_state()
        opponent = state_copy.players[1 - idx_player]
        for ship in opponent.ships:
            ship.location = []
        return state_copy


class RandomPlayer(Player):

    def select_action(self, state: BattleshipGameState, actions: List[BattleshipAction]) -> Optional[BattleshipAction]:
        """ Given masked game state and possible actions, select the next action """
        if len(actions) > 0:
            return random.choice(actions)
        return None


if __name__ == "__main__":

    # Initialize the game
    game = Battleship()
    # Print the initial game state
    game.print_state()

    # Main game loop: Continue until the game reaches the FINISHED phase
    while game.state.phase != GamePhase.FINISHED:
        # Get the list of possible actions for the active player
        actions = game.get_list_action()

        if actions:  # If there are valid actions to take
            # Get the active player's state
            active_player = game.state.players[game.state.idx_player_active]

            # Print whose turn it is
            print(f"\n{active_player.name}'s Turn:")

            # Randomly select an action from the list of possible actions
            action = random.choice(actions)

            # Describe the action being taken
            if action.action_type == ActionType.SET_SHIP:
                print(f"Placing ship {action.ship_name} at {action.location}")
            elif action.action_type == ActionType.SHOOT:
                print(f"Shooting at {action.location}")

            # Apply the selected action to the game state
            game.apply_action(action)

            # Print the updated game state after the action
            game.print_state()

    # Once the loop exits, the game is over, and a winner is determined
    print(f"\nGame Over! Winner: Player {game.state.winner + 1}")