"""Tests pour le coordinateur "Trois petits chats".

Tous les tests unitaires mockent les appels HTTP A2A et le LLM vérificateur,
donc aucune clé API réelle ni agent en cours d'exécution n'est nécessaire.

Markers :
  - (aucun)       : tests unitaires purs, mock total — `pytest -m "not integration and not gemini"`
  - @gemini       : agents mockés + vrai Gemini pour le vérificateur — `pytest -m gemini`
  - @integration  : coordinateur complet contre les vrais agents A2A — `pytest -m integration`
"""
from __future__ import annotations

import os
import sys
import json
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch, call

import pytest

# Ensure the repo root is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

# Provide a dummy API key so module-level env checks pass
os.environ.setdefault("GOOGLE_STUDIO_API_KEY", "test-key")

# ---------------------------------------------------------------------------
# La séquence canonique de "Trois petits chats" (10 vers au total)
# ---------------------------------------------------------------------------
CANONICAL_SEQUENCE = [
    "Trois petits chats",       # initial (turn 0)
    "Chapeau de paille",        # ag2, turn 1
    "Paillasson",               # crewai, turn 2
    "Somnambule",               # langgraph, turn 3
    "Bulletin",                 # ag2, turn 4
    "Tintamarre",               # crewai, turn 5
    "Marabout",                 # langgraph, turn 6
    "Bout de ficelle",          # ag2, turn 7
    "Selle de cheval",          # crewai, turn 8
    "Cheval de course",         # langgraph, turn 9
]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _a2a_response(text: str) -> MagicMock:
    """Construit un objet httpx.Response simulé pour une réponse A2A texte."""
    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json.return_value = {
        "jsonrpc": "2.0",
        "id": "test-id",
        "result": {
            "parts": [{"kind": "text", "text": text}],
        },
    }
    return mock_resp


def _make_mock_http_client(answers: list[str]) -> tuple[MagicMock, list[str]]:
    """
    Retourne un mock httpx.AsyncClient.post qui retourne `answers` en séquence.
    Aussi retourne la liste des URLs appelées pour inspection.
    """
    called_urls: list[str] = []
    call_index = [0]

    async def mock_post(url: str, **kwargs: Any) -> MagicMock:
        called_urls.append(url)
        idx = call_index[0]
        call_index[0] += 1
        return _a2a_response(answers[idx])

    mock_client = MagicMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.post = mock_post

    return mock_client, called_urls


# ---------------------------------------------------------------------------
# Tests du coordinateur
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_routing_order_is_round_robin() -> None:
    """Les 9 appels suivent l'ordre ag2 → crewai → langgraph × 3."""
    from tests.coordinator import coordinator_graph as cg

    answers = CANONICAL_SEQUENCE[1:]  # 9 réponses
    mock_client, called_urls = _make_mock_http_client(answers)

    with patch("tests.coordinator.coordinator_graph.RhymeVerifier") as mock_verifier_cls, \
         patch("httpx.AsyncClient", return_value=mock_client):
        mock_verifier_cls.return_value.verify = AsyncMock(
            return_value={"valid": True, "errors": [], "summary": "OK"}
        )
        state = cg.initial_state()
        result = await cg.graph.ainvoke(state)

    urls = cg._agent_urls()
    expected_url_order = [urls["ag2"], urls["crewai"], urls["langgraph"]] * 3
    assert called_urls == expected_url_order, (
        f"Ordre d'appel incorrect.\nAttendu : {expected_url_order}\nObtenu : {called_urls}"
    )


@pytest.mark.asyncio
async def test_each_agent_called_exactly_3_times() -> None:
    """Chaque agent est appelé exactement 3 fois."""
    from tests.coordinator import coordinator_graph as cg

    answers = CANONICAL_SEQUENCE[1:]
    mock_client, _ = _make_mock_http_client(answers)

    with patch("tests.coordinator.coordinator_graph.RhymeVerifier") as mock_verifier_cls, \
         patch("httpx.AsyncClient", return_value=mock_client):
        mock_verifier_cls.return_value.verify = AsyncMock(
            return_value={"valid": True, "errors": [], "summary": "OK"}
        )
        state = cg.initial_state()
        result = await cg.graph.ainvoke(state)

    assert result["agent_counts"] == {"ag2": 3, "crewai": 3, "langgraph": 3}


@pytest.mark.asyncio
async def test_sequence_has_10_elements() -> None:
    """La séquence finale contient 10 éléments (vers initial + 9 réponses)."""
    from tests.coordinator import coordinator_graph as cg

    answers = CANONICAL_SEQUENCE[1:]
    mock_client, _ = _make_mock_http_client(answers)

    with patch("tests.coordinator.coordinator_graph.RhymeVerifier") as mock_verifier_cls, \
         patch("httpx.AsyncClient", return_value=mock_client):
        mock_verifier_cls.return_value.verify = AsyncMock(
            return_value={"valid": True, "errors": [], "summary": "OK"}
        )
        state = cg.initial_state()
        result = await cg.graph.ainvoke(state)

    assert len(result["sequence"]) == 10, (
        f"Attendu 10 vers, obtenu {len(result['sequence'])}: {result['sequence']}"
    )


@pytest.mark.asyncio
async def test_sequence_starts_with_trois_petits_chats() -> None:
    """La séquence commence par 'Trois petits chats'."""
    from tests.coordinator import coordinator_graph as cg

    answers = CANONICAL_SEQUENCE[1:]
    mock_client, _ = _make_mock_http_client(answers)

    with patch("tests.coordinator.coordinator_graph.RhymeVerifier") as mock_verifier_cls, \
         patch("httpx.AsyncClient", return_value=mock_client):
        mock_verifier_cls.return_value.verify = AsyncMock(
            return_value={"valid": True, "errors": [], "summary": "OK"}
        )
        state = cg.initial_state()
        result = await cg.graph.ainvoke(state)

    assert result["sequence"][0] == "Trois petits chats"


@pytest.mark.asyncio
async def test_verifier_called_with_full_sequence() -> None:
    """RhymeVerifier.verify est appelé avec les 10 vers complets."""
    from tests.coordinator import coordinator_graph as cg

    answers = CANONICAL_SEQUENCE[1:]
    mock_client, _ = _make_mock_http_client(answers)

    with patch("tests.coordinator.coordinator_graph.RhymeVerifier") as mock_verifier_cls, \
         patch("httpx.AsyncClient", return_value=mock_client):
        mock_verify = AsyncMock(return_value={"valid": True, "errors": [], "summary": "OK"})
        mock_verifier_cls.return_value.verify = mock_verify
        state = cg.initial_state()
        await cg.graph.ainvoke(state)

    mock_verify.assert_awaited_once()
    called_sequence = mock_verify.call_args[0][0]
    assert len(called_sequence) == 10
    assert called_sequence[0] == "Trois petits chats"


@pytest.mark.asyncio
async def test_verification_stored_in_state() -> None:
    """L'état final contient le résultat du vérificateur dans 'verification'."""
    from tests.coordinator import coordinator_graph as cg

    answers = CANONICAL_SEQUENCE[1:]
    mock_client, _ = _make_mock_http_client(answers)
    expected_verification = {"valid": True, "errors": [], "summary": "Séquence correcte"}

    with patch("tests.coordinator.coordinator_graph.RhymeVerifier") as mock_verifier_cls, \
         patch("httpx.AsyncClient", return_value=mock_client):
        mock_verifier_cls.return_value.verify = AsyncMock(return_value=expected_verification)
        state = cg.initial_state()
        result = await cg.graph.ainvoke(state)

    assert result["verification"] == expected_verification


# ---------------------------------------------------------------------------
# Tests du vérificateur
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_verifier_returns_valid_for_correct_sequence() -> None:
    """RhymeVerifier retourne valid=True pour une séquence correcte (LLM mocké)."""
    from tests.coordinator.verifier import RhymeVerifier

    mock_response = MagicMock()
    mock_response.content = '{"valid": true, "errors": [], "summary": "Séquence correcte"}'

    with patch("tests.coordinator.verifier.ChatGoogleGenerativeAI") as mock_llm_cls:
        mock_llm = MagicMock()
        mock_llm.ainvoke = AsyncMock(return_value=mock_response)
        mock_llm_cls.return_value = mock_llm
        verifier = RhymeVerifier()
        result = await verifier.verify(CANONICAL_SEQUENCE)

    assert result["valid"] is True
    assert result["errors"] == []


@pytest.mark.asyncio
async def test_verifier_returns_invalid_for_wrong_sequence() -> None:
    """RhymeVerifier retourne valid=False pour une séquence incorrecte (LLM mocké)."""
    from tests.coordinator.verifier import RhymeVerifier

    mock_response = MagicMock()
    mock_response.content = (
        '{"valid": false, "errors": ["vers 3 incohérent : Somnambule ne suit pas Paillasson"], '
        '"summary": "Séquence invalide"}'
    )

    with patch("tests.coordinator.verifier.ChatGoogleGenerativeAI") as mock_llm_cls:
        mock_llm = MagicMock()
        mock_llm.ainvoke = AsyncMock(return_value=mock_response)
        mock_llm_cls.return_value = mock_llm
        verifier = RhymeVerifier()
        bad_sequence = ["Trois petits chats", "Chapeau de paille", "Bonjour"]
        result = await verifier.verify(bad_sequence)

    assert result["valid"] is False
    assert len(result["errors"]) > 0


@pytest.mark.asyncio
async def test_verifier_handles_malformed_llm_response() -> None:
    """RhymeVerifier gère une réponse LLM non-JSON sans lever d'exception."""
    from tests.coordinator.verifier import RhymeVerifier

    mock_response = MagicMock()
    mock_response.content = "Je ne sais pas répondre en JSON."

    with patch("tests.coordinator.verifier.ChatGoogleGenerativeAI") as mock_llm_cls:
        mock_llm = MagicMock()
        mock_llm.ainvoke = AsyncMock(return_value=mock_response)
        mock_llm_cls.return_value = mock_llm
        verifier = RhymeVerifier()
        result = await verifier.verify(CANONICAL_SEQUENCE)

    assert result["valid"] is False
    assert "summary" in result


# ---------------------------------------------------------------------------
# Test de bout-en-bout (intégration — nécessite les agents et la clé API)
# ---------------------------------------------------------------------------

@pytest.mark.integration
@pytest.mark.asyncio
async def test_full_coordination_end_to_end() -> None:
    """Lance le coordinateur complet contre les vrais agents A2A.

    Nécessite :
      - Les 3 agents en fonctionnement (ports 10000, 10001, 10002)
      - GOOGLE_STUDIO_API_KEY défini dans l'environnement
    """
    from tests.coordinator import coordinator_graph as cg

    state = cg.initial_state()
    result = await cg.graph.ainvoke(state)

    # Vérifications structurelles
    assert len(result["sequence"]) == 10
    assert result["sequence"][0] == "Trois petits chats"
    assert result["agent_counts"] == {"ag2": 3, "crewai": 3, "langgraph": 3}

    # Le vérificateur doit avoir produit un résultat
    assert "valid" in result["verification"]
    assert "summary" in result["verification"]


# ---------------------------------------------------------------------------
# Test semi-intégration Gemini (agents mockés, vrai LLM vérificateur)
# ---------------------------------------------------------------------------

@pytest.mark.gemini
@pytest.mark.asyncio
async def test_coordination_with_real_gemini_verifier() -> None:
    """Lance le coordinateur avec les agents A2A mockés et le vrai vérificateur Gemini.

    Les appels HTTP aux 3 agents sont simulés avec la séquence canonique, donc
    aucun agent Docker n'est nécessaire. Seule la clé GOOGLE_STUDIO_API_KEY réelle
    est requise pour appeler Gemini.

    Skip automatique si la clé est absente ou factice.
    """
    real_key = os.environ.get("GOOGLE_STUDIO_API_KEY", "")
    if not real_key or real_key == "test-key":
        pytest.skip("GOOGLE_STUDIO_API_KEY not set or is a dummy key — skipping Gemini test")

    from tests.coordinator import coordinator_graph as cg

    answers = CANONICAL_SEQUENCE[1:]
    mock_client, called_urls = _make_mock_http_client(answers)

    # Only mock the HTTP A2A calls — RhymeVerifier uses the real Gemini LLM
    with patch("httpx.AsyncClient", return_value=mock_client):
        state = cg.initial_state()
        result = await cg.graph.ainvoke(state)

    # Structural checks
    assert len(result["sequence"]) == 10
    assert result["sequence"][0] == "Trois petits chats"
    assert result["agent_counts"] == {"ag2": 3, "crewai": 3, "langgraph": 3}

    # All 9 agent calls were made in round-robin order
    urls = cg._agent_urls()
    assert called_urls == [urls["ag2"], urls["crewai"], urls["langgraph"]] * 3

    # Gemini verifier must have produced a structured result
    verification = result["verification"]
    assert "valid" in verification, f"Verifier did not return 'valid': {verification}"
    assert "summary" in verification, f"Verifier did not return 'summary': {verification}"

    # The canonical sequence is correct — Gemini should agree
    assert verification["valid"] is True, (
        f"Gemini found the canonical sequence invalid:\n"
        f"errors: {verification.get('errors', [])}\n"
        f"summary: {verification.get('summary', '')}\n"
        f"sequence: {result['sequence']}"
    )
