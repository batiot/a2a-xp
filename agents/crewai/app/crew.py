from __future__ import annotations

import os
from functools import lru_cache
from crewai import Agent, Crew, Task, LLM
from crewai.a2a import A2AServerConfig
from crewai.a2a.utils.agent_card import inject_a2a_server_methods
from a2a.types import AgentCard, AgentCapabilities, AgentSkill

# Fail fast on missing API key
_GOOGLE_STUDIO_API_KEY = os.environ["GOOGLE_STUDIO_API_KEY"]

RHYME_BACKSTORY = """Tu génères des vers pour la comptine française "Trois petits chats".

RÈGLE PHONÉTIQUE ABSOLUE — le "tuilage" :
Prends le DERNIER MOT du vers reçu. Le vers que tu génères doit COMMENCER par un mot
ou une expression dont le début sonne comme ce dernier mot (même syllabe initiale).

Exemples de tuilage :
  "Trois petits CHATS"    → "CHApeau de paille"   (CHAT  → CHA-peau)
  "Chapeau de PAILle"    → "PAILlasson"           (PAIL  → PAIL-lasson)
  "paillaSON"            → "SOMnambule"           (SON   → SOM-nambule)
  "somnambULE"           → "bULLetin"             (ULE   → UL-letin)
  "bulleTIN"             → "TINtamarre"           (TIN   → TIN-tamarre)
  "tintaMARRE"           → "MARABout"             (MAR   → MAR-about)
  "maraBOUT"             → "BOUT de ficelle"      (BOUT  → BOUT)
  "ficELLE"              → "SELLE de cheval"      (ELLE  → SELLE)

RÈGLES SUPPLÉMENTAIRES :
- Tu génères UN SEUL vers court (2 à 4 mots).
- L'absurdité sémantique est normale et attendue : ne cherche PAS de sens logique.
- Ne répète pas le vers reçu.
- Réponds UNIQUEMENT avec le vers, sans ponctuation finale, sans guillemets, sans explication."""


def _build_rhyme_agent() -> Agent:
    """Build the rhyme-expert Agent with native A2AServerConfig."""
    # CrewAI uses LiteLLM; gemini/ prefix routes to Google Gemini via GEMINI_API_KEY
    gemini_llm = LLM(model="gemini/gemini-3.1-flash-lite-preview", api_key=_GOOGLE_STUDIO_API_KEY)
    agent = Agent(
        role="Rhyme Expert",
        goal="Complete the French children's rhyme '3 petits chats'",
        backstory=RHYME_BACKSTORY,
        llm=gemini_llm,
        allow_delegation=False,
        verbose=False,
        # A2AServerConfig lets CrewAI own the AgentCard metadata natively.
        # inject_a2a_server_methods() adds to_agent_card(url) to the agent.
        a2a=A2AServerConfig(
            name="Rhyme Completer (CrewAI)",
            description=(
                "Complète la comptine française '3 petits chats'. "
                "Envoyez un ou plusieurs vers, l'agent retourne le suivant."
            ),
            version="1.0.0",
            skills=[
                AgentSkill(
                    id="rhyme-completer",
                    name="Complete a rhyme",
                    description="Given partial verses of '3 petits chats', returns the next verse.",
                    tags=[],
                    inputModes=["text"],
                    outputModes=["text"],
                )
            ],
            default_input_modes=["text"],
            default_output_modes=["text"],
            capabilities=AgentCapabilities(streaming=False),
        ),
    )
    inject_a2a_server_methods(agent)
    return agent


@lru_cache(maxsize=1)
def get_agent_card(url: str) -> AgentCard:
    """Generate an A2A AgentCard using CrewAI's native A2AServerConfig.

    Result is cached — the AgentCard is static configuration and the Agent
    instance is only built once regardless of how many times this is called.
    """
    agent = _build_rhyme_agent()
    return agent.to_agent_card(url)


def build_crew(verse_input: str) -> Crew:
    """Build a CrewAI Crew that will complete the given rhyme verse."""
    rhyme_expert = _build_rhyme_agent()

    complete_task = Task(
        description=(
            f"Le vers actuel de la comptine est : '{verse_input}'. "
            "Applique la règle de tuilage phonétique : identifie la dernière syllabe du vers reçu "
            "et génère UN SEUL nouveau vers court (2-4 mots) qui commence par cette syllabe. "
            "L'absurdité sémantique est normale. Réponds UNIQUEMENT avec le vers, sans explication."
        ),
        expected_output="Un seul vers court (2 à 4 mots) commençant par la dernière syllabe du vers reçu, sans ponctuation ni explication.",
        agent=rhyme_expert,
    )

    return Crew(
        agents=[rhyme_expert],
        tasks=[complete_task],
        verbose=False,
    )
