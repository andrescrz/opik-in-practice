from crewai import Crew, Process

from renovation_planner.agents import build_agents
from renovation_planner.tasks import build_tasks


def build_crew() -> Crew:
    agents = build_agents()
    return Crew(
        agents=list(agents.values()),
        tasks=build_tasks(agents),
        process=Process.sequential,
        verbose=True,
    )
