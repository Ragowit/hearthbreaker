# This is a very simple implementation of the UCT Monte Carlo Tree Search algorithm in Python 2.7.
# The function UCT(rootstate, itermax, verbose = False) is towards the bottom of the code.
# It aims to have the clearest and simplest possible code, and for the sake of clarity, the code
# is orders of magnitude less efficient than it could be made, particularly by using a 
# state.GetRandomMove() or state.DoRandomRollout() function.
# 
# Example GameState classes for Nim, OXO and Othello are included to give some idea of how you
# can write your own GameState use UCT in your 2-player game. Change the game to be played in 
# the UCTPlayGame() function at the bottom of the code.
# 
# Written by Peter Cowling, Ed Powley, Daniel Whitehouse (University of York, UK) September 2012.
# 
# Licence is granted to freely use and distribute for any sensible/legal purpose so long as this comment
# remains in any distributed code.
# 
# For more information about Monte Carlo Tree Search check out our web site at www.mcts.ai

from math import *
import random
import time
from tests.testing_utils import generate_game_for
from hearthbreaker.cards import *
from hearthbreaker.agents.basic_agents import DoNothingAgent
from hearthbreaker.game_objects import *
from hearthbreaker.replay import *


class HearthState:
    """ A state of the game, i.e. the game board.
    """
    def __init__(self):
        self.playerJustMoved = 2 # At the root pretend the player just moved is p2 - p1 has the first move
        deck1 = [GoldshireFootman, GoldshireFootman, MurlocRaider, MurlocRaider, BloodfenRaptor, BloodfenRaptor,
                 FrostwolfGrunt, FrostwolfGrunt, RiverCrocolisk, RiverCrocolisk, IronfurGrizzly, IronfurGrizzly,
                 MagmaRager, MagmaRager, SilverbackPatriarch, SilverbackPatriarch, ChillwindYeti, ChillwindYeti,
                 OasisSnapjaw, OasisSnapjaw, SenjinShieldmasta, SenjinShieldmasta, BootyBayBodyguard, BootyBayBodyguard,
                 FenCreeper, FenCreeper, BoulderfistOgre, BoulderfistOgre, WarGolem, WarGolem]
        #deck2 = [GoldshireFootman, GoldshireFootman, MurlocRaider, MurlocRaider, BloodfenRaptor, BloodfenRaptor,
        #         FrostwolfGrunt, FrostwolfGrunt, RiverCrocolisk, RiverCrocolisk, IronfurGrizzly, IronfurGrizzly,
        #         MagmaRager, MagmaRager, SilverbackPatriarch, SilverbackPatriarch, ChillwindYeti, ChillwindYeti,
        #         OasisSnapjaw, OasisSnapjaw, SenjinShieldmasta, SenjinShieldmasta, BootyBayBodyguard, BootyBayBodyguard,
        #         FenCreeper, FenCreeper, BoulderfistOgre, BoulderfistOgre, WarGolem, WarGolem]
        #deck1 = RiverCrocolisk
        #deck1 = [Innervate, Innervate, WildGrowth, WildGrowth, Wrath, Wrath]
        #deck1 = [Soulfire, Soulfire]
        #deck1 = [Soulfire, Soulfire, MortalCoil, MortalCoil]
        #deck2 = RiverCrocolisk
        deck2 = [Backstab, Backstab, Shadowstep, Shadowstep, Shiv, Shiv, AnubarAmbusher, AnubarAmbusher, Assassinate,
                 Assassinate, Vanish, Vanish, AmaniBerserker, AmaniBerserker, MadBomber, MadBomber, YouthfulBrewmaster,
                 YouthfulBrewmaster, AcolyteOfPain, AcolyteOfPain, QuestingAdventurer, RagingWorgen, RagingWorgen,
                 AncientBrewmaster, AncientBrewmaster, DefenderOfArgus, DefenderOfArgus, GurubashiBerserker,
                 GurubashiBerserker, RagnarosTheFirelord]
        random.seed(1857)
        game = generate_game_for(deck1, deck2, DoNothingAgent, DoNothingAgent)
        game._start_turn()
        self.game = game

    def Clone(self):
        """ Create a deep clone of this game state.
        """
        st = HearthState()
        st.playerJustMoved = self.playerJustMoved
        st.game = self.game.copy()
        #st.game = copy.copy(self.game.copy())
        #st.game = copy.deepcopy(self.game.copy())
        return st

    def DoMove(self, move):
        """ Update a state by carrying out the given move.
            Must update playerJustMoved if end_turn.
        """
        assert self.game.players[0].hero.health > 0 and self.game.players[1].hero.health > 0 and not self.game.game_ended

        def _choose_target(targets):
            print("*****************************************************************************************")
            print(str(targets))
            print(str(move))
  
            if move[4] is None:
                return None
            else:
                return targets[move[4]]

        def _choose_index(targets, player):
            return move[4]

        def _choose_option(*options):
            return options[move[4]]

        if self.game.current_player.name == "one":
            self.playerJustMoved = 1
        else:
            self.playerJustMoved = 2

        # print(str(self.game.current_player.mana) + "/" + str(self.game.current_player.max_mana))
        if move[0] == "end_turn":
            self.game._end_turn()
            self.game._start_turn()
        elif move[0] == "hero_power":
            self.game.current_player.agent.choose_target = _choose_target
            self.game.current_player.hero.power.use()
        elif move[0] == "summon_minion":
            self.game.current_player.agent.choose_index = _choose_index
            self.game.play_card(self.game.current_player.hand[move[3]])
        elif move[2] is None:  # Passing index rather than object, hopefully the game copy fix will help with this
            self.game.play_card(self.game.current_player.hand[move[3]])
        elif move[0] == "minion_attack":
            self.game.current_player.agent.choose_target = _choose_target
            self.game.current_player.minions[move[3]].attack()
        elif move[0] == "hero_attack":
            self.game.current_player.agent.choose_target = _choose_target
            self.game.current_player.hero.attack()
        elif move[0] == "targeted_spell":
            self.game.current_player.agent.choose_target = _choose_target
            self.game.play_card(self.game.current_player.hand[move[3]])
        else:
            raise NameError("DoMove ran into unclassified card", move)

    def GetMoves(self):
        """ Get all possible moves from this state.
        """
        if self.game.game_ended or self.game.players[0].hero.health <= 0 or self.game.players[1].hero.health <= 0:
            return []
        valid_moves = []  # Move format is [string, attacker/card, target, attacker/card index, target index]

        for card in self.game.current_player.hand:
            dupe = False
            for i in range(len(valid_moves)):
                if valid_moves[i][1].name == card.name:
                    dupe = True
                    break
            if not dupe:
                if card.can_use(self.game.current_player, self.game) and isinstance(card, MinionCard):
                    valid_moves.append(["summon_minion", card, None, self.game.current_player.hand.index(card), 0])
                elif card.can_use(self.game.current_player, self.game) and isinstance(card, WeaponCard):
                    valid_moves.append(["equip_weapon", card, None, self.game.current_player.hand.index(card), 0])
                elif card.can_use(self.game.current_player, self.game) and isinstance(card, SecretCard):
                    valid_moves.append(["played_secret", card, None, self.game.current_player.hand.index(card), 0])
                elif card.can_use(self.game.current_player, self.game) and not card.targetable:
                    valid_moves.append(["untargeted_spell", card, None, self.game.current_player.hand.index(card), 0])
                elif card.can_use(self.game.current_player, self.game) and card.targetable:
                    for i in range(len(card.targets)):
                        valid_moves.append(["targeted_spell", card, card.targets[i],
                                            self.game.current_player.hand.index(card), i])

        found_taunt = False
        targets = []
        for enemy in copy.copy(self.game.other_player.minions):
            if enemy.taunt and enemy.can_be_attacked():
                found_taunt = True
            if enemy.can_be_attacked():
                targets.append(enemy)

        if found_taunt:
            targets = [target for target in targets if target.taunt]
        else:
            targets.append(self.game.other_player.hero)

        for minion in copy.copy(self.game.current_player.minions):
            if minion.can_attack():
                for i in range(len(targets)):
                    valid_moves.append(["minion_attack", minion, targets[i],
                                        self.game.current_player.minions.index(minion), i])

        if self.game.current_player.hero.can_attack():
            for i in range(len(targets)):
                valid_moves.append(["hero_attack", self.game.current_player.hero, targets[i], None, i])

        if (self.game.current_player.hero.power.__str__() == "Fireblast" or \
           self.game.current_player.hero.power.__str__() == "Mind Spike" or \
           self.game.current_player.hero.power.__str__() == "Mind Shatter" or \
           self.game.current_player.hero.power.__str__() == "Lesser Heal") and \
           self.game.current_player.hero.power.can_use():
            for target in hearthbreaker.targeting.find_spell_target(self.game, lambda t: t.spell_targetable()):
                valid_moves.append(["hero_power", self.game.current_player.hero, target, 0, \
                                   hearthbreaker.targeting.find_spell_target(self.game, lambda t: \
                                                                            t.spell_targetable()).index(target)])
        elif self.game.current_player.hero.power.can_use():
            valid_moves.append(["hero_power", self.game.current_player.hero, None, None, None])

        valid_moves.append(["end_turn", None, None])
        return valid_moves
    
    def GetResult(self, playerjm):
        """ Get the game result from the viewpoint of playerjm. 
        """
        if self.game.players[0].hero.health <= 0 and self.game.players[1].hero.health <= 0:
            return 0.5
        elif self.game.players[playerjm - 1].hero.health <= 0:
            return 0
        elif self.game.players[2 - playerjm].hero.health <= 0:
            return 1
        else:  # Should not be possible to get here unless we terminate the game early.
            return 0.5

    def __repr__(self):
        s = "Turn: " + str(self.game.turn)
        s += "\n[" + str(self.game.players[0].hero.health) + " hp:" + str(len(self.game.players[0].hand)) + " in hand:" + str(self.game.players[0].deck.left) + " in deck:" + str(self.game.players[0].mana) + "/" + str(self.game.players[0].max_mana) + " mana] "
        for minion in copy.copy(self.game.players[0].minions):
            s += str(minion.calculate_attack()) + "/" + str(minion.health) + ":"
        s += "\n[" + str(self.game.players[1].hero.health) + " hp:" + str(len(self.game.players[1].hand)) + " in hand:" + str(self.game.players[1].deck.left) + " in deck:" + str(self.game.players[1].mana) + "/" + str(self.game.players[1].max_mana) + " mana] "
        for minion in copy.copy(self.game.players[1].minions):
            s += str(minion.calculate_attack()) + "/" + str(minion.health) + ":"
        s += "\n" + "Current Player: " + str(self.game.current_player.name)
        return s


class Node:
    """ A node in the game tree. Note wins is always from the viewpoint of playerJustMoved.
        Crashes if state not specified.
    """
    def __init__(self, move = None, parent = None, state = None):
        self.move = move # the move that got us to this node - "None" for the root node
        self.parentNode = parent # "None" for the root node
        self.childNodes = []
        self.wins = 0
        self.visits = 0
        self.untriedMoves = state.GetMoves() # future child nodes
        self.playerJustMoved = state.playerJustMoved # the only part of the state that the Node needs later
        
    def UCTSelectChild(self):
        """ Use the UCB1 formula to select a child node. Often a constant UCTK is applied so we have
            lambda c: c.wins/c.visits + UCTK * sqrt(2*log(self.visits)/c.visits to vary the amount of
            exploration versus exploitation.
        """
        s = sorted(self.childNodes, key = lambda c: c.wins/c.visits + sqrt(2*log(self.visits)/c.visits))[-1]
        return s
    
    def AddChild(self, m, s):
        """ Remove m from untriedMoves and add a new child node for this move.
            Return the added child node
        """
        n = Node(move = m, parent = self, state = s)
        self.untriedMoves.remove(m)
        self.childNodes.append(n)
        return n
    
    def Update(self, result):
        """ Update this node - one additional visit and result additional wins. result must be from the viewpoint of playerJustmoved.
        """
        self.visits += 1
        self.wins += result

    def __repr__(self):
        return "[M:" + str(self.move) + " W/V:" + str(self.wins) + "/" + str(self.visits) + " U:" + str(self.untriedMoves) + "]"

    def TreeToString(self, indent):
        s = self.IndentString(indent) + str(self)
        for c in self.childNodes:
             s += c.TreeToString(indent+1)
        return s

    def IndentString(self,indent):
        s = "\n"
        for i in range (1,indent+1):
            s += "| "
        return s

    def ChildrenToString(self):
        s = ""
        for c in self.childNodes:
             s += str(c) + "\n"
        return s[:-2]


def UCT(rootstate, seconds, verbose = False):
    """ Conduct a UCT search for seconds starting from rootstate.
        Return the best move from the rootstate.
        Assumes 2 alternating players (player 1 starts), with game results in the range [0.0, 1.0]."""
    rootnode = Node(state = rootstate)

    future = time.time() + seconds
    while time.time() < future:
        node = rootnode
        state = rootstate.Clone()

        # Select
        while node.untriedMoves == [] and node.childNodes != []: # node is fully expanded and non-terminal
            node = node.UCTSelectChild()
            state.DoMove(node.move)

        # Expand
        if node.untriedMoves != []: # if we can expand (i.e. state/node is non-terminal)
            m = random.choice(node.untriedMoves)
            state.DoMove(m)
            node = node.AddChild(m, state) # add child and descend tree

        # Rollout - this can often be made orders of magnitude quicker using a state.GetRandomMove() function
        while state.GetMoves() != []: # while state is non-terminal
            state.DoMove(random.choice(state.GetMoves()))

        # Backpropagate
        while node != None: # backpropagate from the expanded node and work back to the root node
            node.Update(state.GetResult(node.playerJustMoved)) # state is terminal. Update node with result from POV of node.playerJustMoved
            node = node.parentNode

    # Output some information about the tree - can be omitted
    if (verbose): print(rootnode.TreeToString(0))
    else: print(rootnode.ChildrenToString())

    return sorted(rootnode.childNodes, key = lambda c: c.visits)[-1].move # return the move that was most visited


def UCTPlayGame():
    """ Play a sample game between two UCT players where each player gets a different number 
        of UCT iterations (= simulations = tree nodes).
    """
    state = HearthState()
    while (state.GetMoves() != []):
        print(str(state))
        m = UCT(rootstate = state, seconds = 60, verbose = False)
        print("Best Move: " + str(m) + "\n")
        state.DoMove(m)
    if state.GetResult(state.playerJustMoved) == 1.0:
        print("Player " + str(state.playerJustMoved) + " wins!")
    elif state.GetResult(state.playerJustMoved) == 0.0:
        print("Player " + str(3 - state.playerJustMoved) + " wins!")
    else: print("Nobody wins!")


if __name__ == "__main__":
    """ Play a single game to the end using UCT for both players. 
    """
    UCTPlayGame()
