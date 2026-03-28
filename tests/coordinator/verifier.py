"""Vérificateur de la séquence "Trois petits chats".

Appelle un LLM Gemini pour valider que la séquence produite par les agents
respecte les règles phonétiques de la comptine.
"""
from __future__ import annotations

import json
import os
import re

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage

VERIFIER_PROMPT = """Tu es un expert de la comptine française "Trois petits chats" et du jeu de tuilage phonétique.
On te donne une séquence de vers produite par plusieurs agents IA.

RÈGLE DE TUILAGE : La dernière syllabe du vers N doit être la première syllabe du vers N+1.
Exemples valides :
  "Trois petits CHATS" → "CHApeau de paille"  ✓  (CHA)
  "Chapeau de PAILle" → "PAILlasson"          ✓  (PAIL)
  "paillaSON"         → "SOMnambule"          ✓  (SON→SOM, phonétiquement proches)
  "somnambULE"        → "bULLetin"            ✓  (ULE→UL)
  "bulleTIN"          → "TINtamarre"          ✓  (TIN)
  "tintaMARRE"        → "MARABout"            ✓  (MAR)
  "maraBOUT"          → "BOUT de ficelle"     ✓  (BOUT)
  "ficELLE"           → "SELLE de cheval"     ✓  (ELLE→SELLE)
  "cheVAL"            → "VALse" ou similaire  ✓  (VAL)

IMPORTANT : L'absurdité sémantique est NORMALE et attendue dans cette comptine.
Juge uniquement le lien phonétique, pas la cohérence du sens.
Sois clément : une approximation phonétique proche (ex. "-son" → "som-") est acceptée.

La séquence doit commencer par "Trois petits chats".

Séquence à vérifier (un vers par ligne) :
{sequence}

Réponds UNIQUEMENT avec un objet JSON valide, sans markdown, sans explication :
{{"valid": true|false, "errors": ["vers N : attendu début proche de X, obtenu Y"], "summary": "résumé court"}}"""


class RhymeVerifier:
    """Agent vérificateur basé sur Gemini."""

    def __init__(self) -> None:
        api_key = os.environ["GOOGLE_STUDIO_API_KEY"]
        self._llm = ChatGoogleGenerativeAI(
            model="gemini-3.1-flash-lite-preview",
            google_api_key=api_key,
            temperature=0,
        )

    async def verify(self, sequence: list[str]) -> dict:
        """Vérifie la séquence et retourne {"valid", "errors", "summary"}."""
        numbered = "\n".join(f"{i + 1}. {verse}" for i, verse in enumerate(sequence))
        prompt = VERIFIER_PROMPT.format(sequence=numbered)
        response = await self._llm.ainvoke([HumanMessage(content=prompt)])
        content = response.content
        # langchain-google-genai may return content as a list of content blocks
        if isinstance(content, list):
            content = "".join(
                block["text"] for block in content
                if isinstance(block, dict) and block.get("type") == "text"
            )
        return _parse_verifier_response(content)


def _parse_verifier_response(content: str) -> dict:
    """Extrait le JSON de la réponse du LLM, robuste aux balises markdown."""
    # Strip possible ```json ... ``` wrapper
    match = re.search(r"\{.*\}", content, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass
    return {"valid": False, "errors": [f"Réponse LLM non parsable: {content!r}"], "summary": "parse error"}
