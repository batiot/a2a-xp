from __future__ import annotations

import os
from crewai import Agent, Crew, Task, LLM

# Fail fast on missing API key
_GOOGLE_STUDIO_API_KEY = os.environ["GOOGLE_STUDIO_API_KEY"]

RHYME_BACKSTORY = """Tu es un expert des comptines françaises pour enfants,
en particulier '3 petits chats'. Tu connais chaque vers par cœur.
Tu réponds UNIQUEMENT avec le vers suivant, sans explication."""


def build_crew(verse_input: str) -> Crew:
    """Build a CrewAI Crew that will complete the given rhyme verse."""
    # CrewAI uses LiteLLM; gemini/ prefix routes to Google Gemini via GEMINI_API_KEY
    gemini_llm = LLM(model="gemini/gemini-3.1-flash-lite-preview", api_key=_GOOGLE_STUDIO_API_KEY)
    rhyme_expert = Agent(
        role="Rhyme Expert",
        goal="Complete the French children's rhyme '3 petits chats'",
        backstory=RHYME_BACKSTORY,
        llm=gemini_llm,
        allow_delegation=False,
        verbose=False,
    )

    complete_task = Task(
        description=(
            f"Given these verse(s) of the rhyme: '{verse_input}', "
            "return ONLY the next verse. No explanation, no extra text."
        ),
        expected_output="The next verse of the rhyme, as a single line of text.",
        agent=rhyme_expert,
    )

    return Crew(
        agents=[rhyme_expert],
        tasks=[complete_task],
        verbose=False,
    )
