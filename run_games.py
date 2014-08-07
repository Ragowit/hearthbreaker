import re
from hearthbreaker.agents.basic_agents import RandomAgent
from hearthbreaker.constants import CHARACTER_CLASS
from hearthbreaker.game_objects import Game, card_lookup, Deck
from hearthbreaker.cards import *
import timeit


def load_deck(filename):
    deck_file = open(filename, "r")
    contents = deck_file.read()
    items = re.split('\n', contents)
    cards = []
    character_class = CHARACTER_CLASS.MAGE
    for line in items[0:]:
        line = line.strip(" \n\t\r")
        parts = line.split(" ", 1)
        count = int(parts[0])
        for i in range(0, count):
            card = card_lookup(parts[1])
            if card.character_class != CHARACTER_CLASS.ALL:
                character_class = card.character_class
            cards.append(card)

    deck_file.close()

    return Deck(cards, character_class)


def do_stuff():
    def play_game():
        new_game = game.copy()
        new_game.start()

    deck1 = load_deck("example.hsdeck")
    deck2 = load_deck("example.hsdeck")
    game = Game([deck1, deck2], [RandomAgent(), RandomAgent()])
    game.start()

    print(timeit.timeit(play_game, 'gc.enable()', number=1000))

if __name__ == "__main__":
    do_stuff()
