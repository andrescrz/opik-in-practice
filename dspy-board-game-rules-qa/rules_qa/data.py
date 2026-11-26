import dspy

from .rulebook import load_rulebook

# (question, answer in house format, section id, key fact the answer must contain)
TRAIN = [
    ("How many glow points win the game?",
     "12 glow points [§1.1]", "1.1", "12"),
    ("How many cards do you draw each turn?",
     "2 cards [§2.2]", "2.2", "2"),
    ("What is the hand limit?",
     "7 cards [§2.2]", "2.2", "7"),
    ("How far can a boat move in the Float phase?",
     "Up to 3 tiles [§2.3]", "2.3", "3 tiles"),
    ("How many glow points does lighting a tile score?",
     "2 glow points [§3.1]", "3.1", "2"),
    ("How many oil tokens do you gain when you refill?",
     "3 oil tokens [§3.3]", "3.3", "3"),
    ("What does a Fog card do?",
     "Cancels an opponent's movement for that turn [§4.2]", "4.2", "cancel"),
    ("Who wins if two players hit 12 points in the same round?",
     "The player with the most oil left [§4.3]", "4.3", "most oil"),
]

# Held-out questions: none appear in TRAIN, so demos have to transfer.
# (question, correct section id, assertion pinning the expected fact)
TEST = [
    ("Who takes the first turn?", "1.2",
     "The answer says the youngest player goes first"),
    ("What are the three phases of a turn?", "2.1",
     "The answer lists Draw, Float and Light in that order"),
    ("What does crossing a bridge tile cost?", "2.3",
     "The answer says it costs 1 oil token"),
    ("How do you light a tile?", "3.1",
     "The answer says to play a lantern card matching the tile's color"),
    ("What happens when the wind die shows a 1?", "3.2",
     "The answer says a lit lantern goes out and you lose 1 glow point"),
    ("What is the most oil a player can hold?", "3.3",
     "The answer says 6 oil tokens"),
    ("Can players trade oil tokens?", "4.1",
     "The answer says no, oil can never be traded"),
    ("What does playing a Fog card cost?", "4.2",
     "The answer says it costs 1 oil token"),
]


def build_trainset() -> list[dspy.Example]:
    rulebook = load_rulebook()
    return [
        dspy.Example(rulebook=rulebook, question=question, answer=answer,
                     section=section, key_fact=fact).with_inputs("rulebook", "question")
        for question, answer, section, fact in TRAIN
    ]
