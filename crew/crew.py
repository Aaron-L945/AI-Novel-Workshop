# crew/crew.py
from crewai import Crew


def build_crew(agents, tasks):
    return Crew(
        agents=agents,
        tasks=tasks,
        process="sequential",
        verbose=True,
    )
