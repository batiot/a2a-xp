## 1. Scaffolding du répertoire coordinateur

- [ ] 1.1 Créer `tests/coordinator/__init__.py` (fichier vide)
- [ ] 1.2 Créer `tests/coordinator/requirements.txt` avec les dépendances pinnées : `langgraph`, `langchain-google-genai`, `langchain-core`, `httpx`, `pytest`, `pytest-asyncio`, `a2a-sdk` (reprendre les versions déjà utilisées dans `agents/langgraph/requirements.txt`)
- [ ] 1.3 Créer `tests/coordinator/pytest.ini` avec `asyncio_mode = auto` et le marker `integration`

## 2. Implémentation du vérificateur

- [ ] 2.1 Créer `tests/coordinator/verifier.py` :
  - Classe `RhymeVerifier` avec méthode `async verify(sequence: list[str]) -> dict`
  - Construit le prompt `VERIFIER_PROMPT` avec la séquence formatée
  - Appelle `ChatGoogleGenerativeAI` (Gemini) et parse la réponse JSON
  - Gère `KeyError` si `GOOGLE_STUDIO_API_KEY` manquant
  - Retourne `{"valid": bool, "errors": list[str], "summary": str}`

## 3. Implémentation du coordinateur LangGraph

- [ ] 3.1 Créer `tests/coordinator/coordinator_graph.py` :
  - Définir `CoordinatorState(TypedDict)` avec `sequence`, `turn`, `agent_counts`, `current_verse`, `done`, `verification`
  - Lire les URLs depuis les variables d'environnement (`AG2_AGENT_URL`, `CREWAI_AGENT_URL`, `LG_AGENT_URL`) avec les defaults `http://localhost:10000/10001/10002`
  - Implémenter `route_node(state)` : calcule `agent_index = turn % 3`, retourne le nom de l'agent suivant (ou `"verify"` si `turn == 9`)
  - Implémenter `call_agent_node(agent_name, url)` : factory qui retourne un nœud async appelant l'agent via `httpx.AsyncClient.post`, extrait le texte de la réponse A2A, met à jour `sequence`, `current_verse`, `turn`, `agent_counts`
  - Implémenter `verify_node(state)` : appelle `RhymeVerifier().verify(state["sequence"])` et stocke le résultat dans `state["verification"]`
  - Construire le `StateGraph` : `START → route_node → conditional_edges → [call_ag2|call_crewai|call_langgraph] → route_node → ... → verify_node → END`
  - Exporter `graph = builder.compile()` et `AGENT_ORDER = ["ag2", "crewai", "langgraph"]`

## 4. Tests

- [ ] 4.1 Créer `tests/coordinator/test_coordinator.py` :
  - **Setup** : fixture `mock_agents` qui patch `httpx.AsyncClient.post` pour retourner la vraie séquence de la comptine en round-robin, et `mock_verifier` qui patch `RhymeVerifier.verify`
  - **Test 1** `test_routing_order_is_round_robin` : vérifie que les 9 appels suivent l'ordre `ag2, crewai, langgraph, ag2, crewai, langgraph, ag2, crewai, langgraph`
  - **Test 2** `test_each_agent_called_exactly_3_times` : vérifie `agent_counts == {"ag2": 3, "crewai": 3, "langgraph": 3}` dans l'état final
  - **Test 3** `test_sequence_has_10_elements` : vérifie que `len(state["sequence"]) == 10` (vers initial + 9 réponses)
  - **Test 4** `test_sequence_starts_with_trois_petits_chats` : vérifie `state["sequence"][0] == "Trois petits chats"`
  - **Test 5** `test_verifier_called_with_full_sequence` : vérifie que `RhymeVerifier.verify` est appelé avec les 10 vers
  - **Test 6** `test_verification_stored_in_state` : vérifie que `state["verification"]` contient le résultat du vérificateur
  - **Test 7** `test_verifier_returns_valid_for_correct_sequence` : instancier `RhymeVerifier` avec LLM mocké retournant `{"valid": true, "errors": [], "summary": "OK"}`, vérifier que `verify()` retourne `valid: True`
  - **Test 8** `test_verifier_returns_invalid_for_wrong_sequence` : LLM mocké retourne `{"valid": false, "errors": ["vers 3 incohérent"], "summary": "KO"}`, vérifier `valid: False`
  - Marker `@pytest.mark.integration` pour un test optionnel de bout-en-bout (skip si agents non disponibles)

## 5. Validation

- [ ] 5.1 Depuis `tests/coordinator/`, créer un venv avec `uv venv` et installer les dépendances
- [ ] 5.2 Lancer `uv run pytest -v` — tous les tests unitaires passent sans clé API réelle
- [ ] 5.3 Vérifier que `test_coordinator.py` n'importe rien depuis les agents existants (isolation complète)
