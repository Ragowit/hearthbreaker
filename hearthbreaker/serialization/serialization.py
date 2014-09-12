import json
from hearthbreaker.cards import StonetuskBoar, FlameImp, LightsJustice, EyeForAnEye
from hearthbreaker.game_objects import Game
from tests.agents.testing_agents import SpellTestingAgent
from tests.testing_utils import generate_game_for


def _save_object(o):
    return o.__json__()

def _load_object(d):
    return Game.__from_json__(d)

def serialize(game):
    """
    Encode the given game instance as a JSON formatted string.  This string can be used to re-construct the game exactly
    as it is now

    :param heartbreaker.game_objects.Game game: The game to serialize
    :rtype: string
    """

    return json.dumps(game, default=_save_object, indent=2)

def deserialize(json_string):
    """
    Decode the given game instance from a JSON formatted string.

    :param string json_string: The string representation of the game
    :rtype: :class:`hearthbreaker.game_objects.Game`
    """
    d = json.loads(json_string)
    return Game.__from_json__(d)


if __name__ == "__main__":
    game = generate_game_for([LightsJustice, EyeForAnEye], FlameImp, SpellTestingAgent, SpellTestingAgent)
    for turn in range(0, 5):
        game.play_single_turn()

    print(serialize(game))
    game2 = deserialize(serialize(game))
    game2.start()