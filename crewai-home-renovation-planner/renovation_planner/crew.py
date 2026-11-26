from crewai import Crew, Process
from opik.integrations.crewai import track_crewai

from renovation_planner.agents import build_agents
from renovation_planner.tasks import build_tasks


PROJECT_NAME = "crewai-home-renovation-planner"


def build_crew() -> Crew:
    agents = build_agents()
    crew = Crew(
        agents=list(agents.values()),
        tasks=build_tasks(agents),
        process=Process.sequential,
        verbose=True,
    )
    # track_crewai hooks CrewAI's event bus: each kickoff becomes ONE trace in the project, with
    # task and agent spans nested inside and llm spans (tokens + cost) at the leaves.
    # Without it the crew runs fine but nothing reaches Opik.
    track_crewai(project_name=PROJECT_NAME, crew=crew)
    return crew
