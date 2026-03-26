## Context

Monorepo `a2a-xp/` avec trois agents A2A déjà opérationnels (AG2 sur port 10000, CrewAI sur port 10001, LangGraph sur port 10002). Chaque agent expose `POST /` (JSON-RPC `message/send`) et `GET /.well-known/agent.json`. Cette implémentation ajoute un coordinateur **sans modifier** les agents existants.

## Goals / Non-Goals

**Goals:**
- Implémenter un coordinateur LangGraph dans `tests/coordinator/` qui orchestre les 3 agents A2A en round-robin.
- Arrêt automatique après 3 tours par agent (9 tours totaux).
- Vérificateur final basé sur un LLM Gemini qui valide la séquence "Trois petits chats".
- Tests unitaires complets (mocks HTTP) + mode intégration optionnel.

**Non-Goals:**
- Modifier les agents existants.
- Ajouter un service Docker pour le coordinateur (c'est un test runner, pas un serveur).
- Implémenter le mode streaming ou multi-turn A2A.
- Changer les ports ou la configuration réseau.

## Decisions

### D1 — Structure du StateGraph coordinateur

Le coordinateur LangGraph utilise un `StateGraph` avec l'état suivant :

```python
class CoordinatorState(TypedDict):
    sequence: list[str]          # vers accumulés depuis le début
    turn: int                    # tour global (0..8)
    agent_counts: dict[str, int] # nb d'appels par agent {"ag2":0,"crewai":0,"langgraph":0}
    current_verse: str           # vers courant à envoyer au prochain agent
    done: bool                   # True quand les 3 agents ont été appelés 3x chacun
```

Le graphe contient :
- **`route`** : nœud de routage — détermine quel agent appeler selon l'ordre round-robin `[ag2, crewai, langgraph]` et incrémente `turn`.
- **`call_ag2`**, **`call_crewai`**, **`call_langgraph`** : nœuds d'appel HTTP A2A asynchrones via `httpx.AsyncClient`.
- **`verify`** : nœud final — appelle le vérificateur LLM sur la séquence complète.
- **`END`** : sortie du graphe.

Transitions :
```
START → route → [call_ag2 | call_crewai | call_langgraph] → route → ... → verify → END
```

La condition d'arrêt est vérifiée dans `route` : si `turn == 9`, rediriger vers `verify`.

### D2 — Protocole A2A dans les nœuds d'appel

Chaque nœud d'appel utilise le JSON-RPC `message/send` standard :

```python
payload = {
    "jsonrpc": "2.0",
    "id": str(uuid.uuid4()),
    "method": "message/send",
    "params": {
        "message": {
            "role": "user",
            "messageId": str(uuid.uuid4()),
            "parts": [{"kind": "text", "text": state["current_verse"]}],
        }
    },
}
```

La réponse est extraite depuis `result.parts[0].text` (ou le premier part de type `text`).

### D3 — Vérificateur final

Le vérificateur est un LLM Gemini invoqué une seule fois avec la séquence complète et les règles :

```python
VERIFIER_PROMPT = """
Tu es un expert de la comptine française "Trois petits chats".
On te donne une séquence de vers produite par plusieurs agents.

Règle : chaque vers doit dériver phonétiquement du précédent (la dernière syllabe
ou le mot final du vers N devient le début du vers N+1).

La séquence commence par "Trois petits chats" et doit, après 9 vers, former
une chaîne cohérente.

Séquence à vérifier :
{sequence}

Réponds en JSON :
{{"valid": true|false, "errors": ["..."], "summary": "..."}}
"""
```

Le vérificateur renvoie un dict `{valid, errors, summary}` stocké dans l'état final.

### D4 — Configuration des URLs agents

Les URLs sont configurables via variables d'environnement pour supporter les deux modes (mock local et vraie stack Docker) :

| Variable          | Défaut                         |
|-------------------|--------------------------------|
| `AG2_AGENT_URL`   | `http://localhost:10000`       |
| `CREWAI_AGENT_URL`| `http://localhost:10001`       |
| `LG_AGENT_URL`    | `http://localhost:10002`       |

### D5 — Tests unitaires

Les tests mockent `httpx.AsyncClient.post` pour simuler les réponses des agents A2A avec la vraie séquence de la comptine. Ils vérifient :

1. Que le routage round-robin respecte l'ordre `ag2 → crewai → langgraph`.
2. Que chaque agent est appelé exactement 3 fois.
3. Que la séquence finale contient exactement 10 éléments (vers initial + 9 réponses).
4. Que le vérificateur est appelé avec la séquence complète.
5. Que le vérificateur retourne `valid: true` pour une séquence correcte.
6. Que le vérificateur retourne `valid: false` pour une séquence incorrecte.

### D6 — Structure des fichiers

```
tests/coordinator/
├── __init__.py
├── coordinator_graph.py   # LangGraph StateGraph coordinateur
├── verifier.py            # Agent vérificateur LLM
├── requirements.txt       # langgraph, langchain-google-genai, httpx, pytest-asyncio, a2a-sdk
├── pytest.ini
└── test_coordinator.py    # Tests unitaires (mocks) + marker @pytest.mark.integration
```

## Risks / Trade-offs

- **[Risk] Les agents LLM ne produisent pas exactement la séquence canonique** — Le vérificateur LLM est flexible sur les variantes phonétiques acceptables, pas seulement la séquence canonique.
- **[Risk] Dépendance à `GOOGLE_STUDIO_API_KEY` en test unitaire** — Mitigé par le mock complet du LLM dans les tests unitaires (pas de vraie clé requise).
- **[Trade-off] Coordinateur comme test runner, pas serveur** — Simplifie l'infrastructure (pas de Docker supplémentaire) mais ne démontre pas le coordinateur comme service A2A lui-même. Acceptable pour un learning lab.
