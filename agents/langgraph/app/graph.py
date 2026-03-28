from __future__ import annotations

import os
from typing import Annotated

from langchain_core.messages import BaseMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict

# Fail fast on missing API key
_GOOGLE_STUDIO_API_KEY = os.environ["GOOGLE_STUDIO_API_KEY"]

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
  "cheVAL"               → "VALse" ou "CHEVAL de course"  (VAL → VAL-...)

RÈGLES SUPPLÉMENTAIRES :
- Tu génères UN SEUL vers court (2 à 4 mots).
- L'absurdité sémantique est normale et attendue : ne cherche PAS de sens logique.
- Ne répète pas le vers reçu.
- Réponds UNIQUEMENT avec le vers, sans ponctuation finale, sans guillemets, sans explication."""


class State(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]


llm = ChatGoogleGenerativeAI(
    model="gemini-3.1-flash-lite-preview",
    google_api_key=_GOOGLE_STUDIO_API_KEY,
    temperature=0,
)


def rhyme_node(state: State) -> dict:
    """Single LLM node: prepend system prompt and call the model."""
    from langchain_core.messages import SystemMessage

    messages = [SystemMessage(content=SYSTEM_PROMPT)] + state["messages"]
    response = llm.invoke(messages)
    return {"messages": [response]}


# Build the graph
builder = StateGraph(State)
builder.add_node("rhyme", rhyme_node)
builder.set_entry_point("rhyme")
builder.add_edge("rhyme", END)

# This `graph` name is referenced in langgraph.json
graph = builder.compile()
