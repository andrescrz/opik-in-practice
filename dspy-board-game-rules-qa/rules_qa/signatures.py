import dspy


class RulesQuestion(dspy.Signature):
    """Answer the player's question using the Lanternfall rulebook."""

    rulebook: str = dspy.InputField(desc="the full Lanternfall rulebook")
    question: str = dspy.InputField()
    answer: str = dspy.OutputField()


# The instruction above says nothing about the answer format on purpose: the
# house style ("<short answer> [§2.2]") only ever appears in the worked
# examples, so only a compiled program with demos can learn it.
