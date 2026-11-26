from crewai import Agent

MODEL = "gpt-4o-mini"


def build_agents() -> dict[str, Agent]:
    return {
        "scope_planner": Agent(
            role="Scope Planner",
            goal="Turn a client brief into a precise, itemized scope of work.",
            backstory=(
                "A renovation project manager who has read ten thousand briefs. "
                "You list only work the client asked for, and quantities only "
                "when the brief or price sheet gives them."
            ),
            llm=MODEL,
        ),
        "budget_estimator": Agent(
            role="Budget Estimator",
            goal="Price every scope item from the price sheet and check it against the ceiling.",
            backstory=(
                "A cost estimator who never invents a price: every line uses a "
                "unit price from the sheet and shows quantity times price."
            ),
            llm=MODEL,
        ),
        "schedule_coordinator": Agent(
            role="Schedule Coordinator",
            goal="Sequence the work into a week-by-week plan that respects every constraint.",
            backstory=(
                "A site coordinator who plans around lead times, elevator "
                "bookings, building rules and the owners' calendar."
            ),
            llm=MODEL,
        ),
    }
