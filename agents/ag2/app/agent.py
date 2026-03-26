from __future__ import annotations

import os

from autogen import AssistantAgent
from autogen.a2a import A2aAgentServer, CardSettings
from a2a.types import AgentCapabilities, AgentSkill

SYSTEM_PROMPT = """Tu es un expert des comptines françaises pour enfants.
Quand on te donne un ou plusieurs vers d'une comptine,
tu réponds UNIQUEMENT avec le vers suivant. Pas d'explication, pas de ponctuation supplémentaire.

Exemple:
Entrée: "3 petits chats"
Sortie: "chapeau de paille"

Exemple:
Entrée: "3 petits chats / chapeau de paille"
Sortie: "paille chapeau"
"""

_CARD_SETTINGS = CardSettings(
    name="Rhyme Completer (AG2)",
    description=(
        "Complète la comptine française '3 petits chats'. "
        "Envoyez un ou plusieurs vers, l'agent retourne le suivant."
    ),
    version="1.0.0",
    capabilities=AgentCapabilities(streaming=False),
    skills=[
        AgentSkill(
            id="rhyme-completer",
            name="Complete a rhyme",
            description="Given partial verses of '3 petits chats', returns the next verse.",
            tags=[],
            input_modes=["text"],
            output_modes=["text"],
        )
    ],
    default_input_modes=["text"],
    default_output_modes=["text"],
)


def build_agent_server(url: str) -> A2aAgentServer:
    """Build a native AG2 A2aAgentServer for the rhyme-completer agent.

    Uses autogen.AssistantAgent with the Google Gemini LLM via the ag2[gemini] extra.
    The A2aAgentServer wraps the agent and handles AgentCard + A2A protocol natively.
    """
    agent = AssistantAgent(
        name="rhyme_completer",
        system_message=SYSTEM_PROMPT,
        description=_CARD_SETTINGS.description,
        llm_config={
            "config_list": [
                {
                    "api_type": "google",
                    "model": "gemini-2.0-flash-lite",
                    "api_key": os.environ["GOOGLE_STUDIO_API_KEY"],
                }
            ]
        },
        human_input_mode="NEVER",
    )
    return A2aAgentServer(
        agent=agent,
        url=url,
        agent_card=_CARD_SETTINGS,
    )
