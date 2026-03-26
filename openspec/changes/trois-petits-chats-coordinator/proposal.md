## Why

Le projet `a2a-xp` démontre comment trois frameworks (AG2, CrewAI, LangGraph) peuvent exposer le même agent via le protocole A2A. Mais jusqu'ici, chaque agent est testé indépendamment par un client séquentiel. Ce change ajoute un **test de coordination A2A** où un agent orchestrateur (LangGraph) distribue une tâche collaborative aux trois agents en parallèle selon un protocole précis.

La comptine **"Trois petits chats"** est une chaîne de mots où chaque vers découle phonétiquement du précédent :

```
Trois petits chats →
Chapeau de paille →
Paillasson →
Somnambule →
Bulletin →
Tintamarre →
Marabout →
Bout de ficelle →
Selle de cheval →
...
```

La règle : chaque vers reprend la dernière syllabe ou le son final du vers précédent pour en former un nouveau. La chaîne est circulaire (le dernier vers ramène à "Trois petits chats").

Ce scénario est idéal pour tester la coordination A2A car :
- La tâche est **déterministe** : si l'agent connaît la comptine, la réponse est prévisible.
- La séquence impose un **ordre strict** des appels inter-agents.
- La vérification finale est **objective** : la chaîne produite doit respecter les règles phonétiques.

## What Changes

- **`tests/coordinator/`** : nouveau répertoire contenant le coordinateur et ses tests.
  - `coordinator_graph.py` : LangGraph StateGraph orchestrant les 3 agents A2A en round-robin, 3 fois chacun (9 tours au total).
  - `verifier.py` : agent LLM (Gemini) vérifiant que la séquence finale respecte les règles de "Trois petits chats".
  - `test_coordinator.py` : tests pytest couvrant la logique du coordinateur (unitaires avec mocks A2A) et la vérification (unitaire avec LLM mocké).

## Capabilities

### New Capabilities

- `trois-petits-chats-coordinator`: Orchestrateur LangGraph qui démarre la comptine et distribue séquentiellement les tours aux 3 agents A2A (ag2 → crewai → langgraph → ag2 → ...) jusqu'à 3 tours par agent (9 au total), puis vérifie la séquence complète.

## Impact

- Aucune modification des agents existants (`agents/ag2/`, `agents/crewai/`, `agents/langgraph/`).
- Nouveau répertoire `tests/coordinator/` avec `requirements.txt`, `pytest.ini`, sources et tests.
- Le test de coordination est **autonome** : il peut être lancé seul via `uv run pytest tests/coordinator/` depuis la racine, ou intégré à la CI.
- En mode intégration (avec `--integration`), le test appelle les vrais agents via HTTP ; sans ce flag, tout est mocké (tests unitaires rapides).
