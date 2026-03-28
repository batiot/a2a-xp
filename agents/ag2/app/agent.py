from __future__ import annotations

import os

from autogen import AssistantAgent
from autogen.a2a import A2aAgentServer, CardSettings
from a2a.types import AgentCapabilities, AgentSkill

SYSTEM_PROMPT = """Tu génères des vers pour la comptine française "Trois petits chats".

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
  "cheVAL"               → "VALse" ou "CHEVAL..." (VAL   → VAL-...)

RÈGLES SUPPLÉMENTAIRES :
- Tu génères UN SEUL vers court (2 à 4 mots).
- L'absurdité sémantique est normale et attendue : ne cherche PAS de sens logique.
- Ne répète pas le vers reçu.
- Réponds UNIQUEMENT avec le vers, sans ponctuation finale, sans guillemets, sans explication.
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
                    "model": "gemini-3.1-flash-lite-preview",
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
