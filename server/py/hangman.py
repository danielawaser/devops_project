from typing import List, Optional
import random
from enum import Enum
from server.py.game import Game, Player

HANGMAN_PICS = [
    '''
     +---+
     |    
     |    
     |    
    ===''', '''
     +---+
     |   O
     |    
     |    
    ===''', '''
     +---+
     |   O
     |   |
     |    
    ===''', '''
     +---+
     |   O
     |  /|
     |    
    ===''', '''
     +---+
     |   O
     |  /|\\
     |    
    ===''', '''
     +---+
     |   O
     |  /|\\
     |    \\
    ===''', '''
     +---+
     |   O
     |  /|\\
     |  / 
    ===''', '''
     +---+
     |   O
     |  /|\\
     |  / \\
    ==='''
]


class GuessLetterAction:

    def __init__(self, letter: str) -> None:
        if len(letter) != 1 or not letter.isalpha():
            raise ValueError("A guess must be a single alphabetic character.")
        self.letter = letter.upper()  # Store in uppercase for consistency

    def __repr__(self) -> str:
        return f"GuessLetterAction(letter='{self.letter}')"


class GamePhase(str, Enum):
    SETUP = 'setup'
    RUNNING = 'running'
    FINISHED = 'finished'


class HangmanGameState:

    def __init__(self, word_to_guess: str, phase: GamePhase, guesses: List[str], incorrect_guesses: List[str]) -> None:
        self.word_to_guess = word_to_guess.upper()  # Normalize to uppercase
        self.phase = phase
        self.guesses = guesses
        self.incorrect_guesses = incorrect_guesses

    def display_state(self) -> None:
        word_display = ''.join([letter if letter in self.guesses else '_' for letter in self.word_to_guess])
        print(f"Word: {word_display}")
        print(f"Incorrect guesses: {', '.join(self.incorrect_guesses)}")
        print(f"Hangman:\n{HANGMAN_PICS[len(self.incorrect_guesses)]}")
        print()


class Hangman(Game):

    def __init__(self) -> None:
        self.state: Optional[HangmanGameState] = None

    def get_state(self) -> HangmanGameState:
        return self.state

    def set_state(self, state: HangmanGameState) -> None:
        self.state = state

    def print_state(self) -> None:
        if self.state:
            self.state.display_state()

    def get_list_action(self) -> List[GuessLetterAction]:
        alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        possible_guesses = [letter for letter in alphabet if letter not in self.state.guesses]
        return [GuessLetterAction(letter) for letter in possible_guesses]

    def apply_action(self, action: GuessLetterAction) -> None:
        if not self.state or self.state.phase != GamePhase.RUNNING:
            return
        letter = action.letter.upper()
        if letter in self.state.word_to_guess:
            if letter not in self.state.guesses:
                self.state.guesses.append(letter)
            if all(l in self.state.guesses for l in self.state.word_to_guess):
                self.state.phase = GamePhase.FINISHED
        else:
            if letter not in self.state.incorrect_guesses:
                self.state.incorrect_guesses.append(letter)
            if len(self.state.incorrect_guesses) >= len(HANGMAN_PICS) - 1:
                self.state.phase = GamePhase.FINISHED

    def get_player_view(self, idx_player: int) -> HangmanGameState:
        word_display = ''.join([letter if letter in self.state.guesses else '_' for letter in self.state.word_to_guess])
        return HangmanGameState(
            word_to_guess=word_display,
            phase=self.state.phase,
            guesses=self.state.guesses,
            incorrect_guesses=self.state.incorrect_guesses
        )


class RandomPlayer(Player):

    def select_action(self, state: HangmanGameState, actions: List[GuessLetterAction]) -> Optional[GuessLetterAction]:
        if actions:
            return random.choice(actions)
        return None


if __name__ == "__main__":

    game = Hangman()

    def setup_game():
        word_list = ['daniela', 'geraldine', 'liliana', 'laura']
        chosen_word = random.choice(word_list)
        game_state = HangmanGameState(word_to_guess=chosen_word, phase=GamePhase.SETUP, guesses=[], incorrect_guesses=[])
        game.set_state(game_state)
        game.state.phase = GamePhase.RUNNING

    setup_game()
    player = RandomPlayer()
    while game.state.phase == GamePhase.RUNNING:
        game.print_state()
        actions = game.get_list_action()
        action = player.select_action(game.state, actions)
        if action:
            game.apply_action(action)

    if game.state.phase == GamePhase.FINISHED:
        game.print_state()
