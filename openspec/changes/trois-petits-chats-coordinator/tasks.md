## 1. Scaffolding du répertoire coordinateur

- [x] 1.1 Créer `tests/coordinator/__init__.py` (fichier vide)
- [x] 1.2 Créer `tests/coordinator/requirements.txt` avec les dépendances pinnées : `langgraph`, `langchain-google-genai`, `langchain-core`, `httpx`, `pytest`, `pytest-asyncio`, `a2a-sdk` (reprendre les versions déjà utilisées dans `agents/langgraph/requirements.txt`)
- [x] 1.3 Créer `tests/coordinator/pytest.ini` avec `asyncio_mode = auto` et le marker `integration`

## 2. Implémentation du vérificateur

- [x] 2.1 Créer `tests/coordinator/verifier.py` :
  - Classe `RhymeVerifier` avec méthode `async verify(sequence: list[str]) -> dict`
  - Construit le prompt `VERIFIER_PROMPT` avec la séquence formatée
  - Appelle `ChatGoogleGenerativeAI` (Gemini) et parse la réponse JSON
  - Gère `KeyError` si `GOOGLE_STUDIO_API_KEY` manquant
  - Retourne `{"valid": bool, "errors": list[str], "summary": str}`

## 3. Implémentation du coordinateur LangGraph

- [x] 3.1 Créer `tests/coordinator/coordinator_graph.py` :
  - Définir `CoordinatorState(TypedDict)` avec `sequence`, `turn`, `agent_counts`, `current_verse`, `verification`
  - Lire les URLs depuis les variables d'environnement (`AG2_AGENT_URL`, `CREWAI_AGENT_URL`, `LG_AGENT_URL`) avec les defaults `http://localhost:10000/10001/10002`
  - Implémenter `route_node(state)` : calcule `agent_index = turn % 3`, retourne le nom de l'agent suivant (ou `"verify"` si `turn == 9`)
  - Implémenter nœuds d'appel async (`call_ag2_node`, `call_crewai_node`, `call_langgraph_node`) appelant l'agent via `httpx.AsyncClient.post`, extrayant le texte de la réponse A2A
  - Implémenter `verify_node(state)` : appelle `RhymeVerifier().verify(state["sequence"])`
  - Construire le `StateGraph` avec `conditional_edges` depuis START et chaque nœud agent
  - Exporter `graph = builder.compile()`, `AGENT_ORDER`, `initial_state()`

## 4. Tests

- [x] 4.1 Créer `tests/coordinator/test_coordinator.py` :
  - **Test 1** `test_routing_order_is_round_robin` ✓
  - **Test 2** `test_each_agent_called_exactly_3_times` ✓
  - **Test 3** `test_sequence_has_10_elements` ✓
  - **Test 4** `test_sequence_starts_with_trois_petits_chats` ✓
  - **Test 5** `test_verifier_called_with_full_sequence` ✓
  - **Test 6** `test_verification_stored_in_state` ✓
  - **Test 7** `test_verifier_returns_valid_for_correct_sequence` ✓
  - **Test 8** `test_verifier_returns_invalid_for_wrong_sequence` ✓
  - **Test 9** `test_verifier_handles_malformed_llm_response` ✓
  - Marker `@pytest.mark.integration` pour test de bout-en-bout (skip par défaut)

## 5. Validation

- [x] 5.1 Dépendances installées via pip dans venv dédié
- [x] 5.2 `pytest -v -m "not integration"` — **9/9 tests unitaires passent** sans clé API réelle
- [x] 5.3 `test_coordinator.py` n'importe rien depuis les agents existants (isolation complète)
