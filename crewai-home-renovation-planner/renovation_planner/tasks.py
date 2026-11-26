from crewai import Agent, Task


def build_tasks(agents: dict[str, Agent]) -> list[Task]:
    scope = Task(
        name="Define the scope",
        description=(
            "Read the client brief below and list the scope of work for the "
            "kitchen and the bathroom. Do not add work the client did not ask "
            "for.\n\nCLIENT BRIEF:\n\n{brief}"
        ),
        expected_output=(
            "Two bullet lists (Kitchen, Bathroom). Each bullet is one work "
            "item with a quantity where the brief or price sheet gives one."
        ),
        agent=agents["scope_planner"],
    )
    budget = Task(
        name="Estimate the budget",
        description=(
            "Price the scope using ONLY the price sheet below. Show each line "
            "as quantity x unit price = subtotal, add a 10% contingency, and "
            "say whether the total fits the client's ceiling.\n\n"
            "PRICE SHEET:\n\n{price_sheet}"
        ),
        expected_output=(
            "A line-item table, a subtotal, the contingency, the grand total, "
            "and one sentence on whether it is under the ceiling."
        ),
        agent=agents["budget_estimator"],
        context=[scope],
    )
    schedule = Task(
        name="Plan the schedule",
        description=(
            "Using the scope, the budget and the constraints in the brief, "
            "build a week-by-week schedule. Use the lead times and typical "
            "labor in the price sheet. Flag anything that cannot fit.\n\n"
            "CLIENT BRIEF:\n\n{brief}\n\nPRICE SHEET:\n\n{price_sheet}"
        ),
        expected_output=(
            "A week-by-week plan (under 250 words) with elevator bookings, "
            "demolition inside the owners' travel window, and a final "
            "paragraph of risks."
        ),
        agent=agents["schedule_coordinator"],
        context=[scope, budget],
    )
    return [scope, budget, schedule]
