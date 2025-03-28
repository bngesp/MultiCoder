# MultiCoder 🚀

## Description
MultiCoder est un assistant de développement en ligne de commande basé sur un système multi-agent. Il permet aux développeurs d'interagir avec plusieurs agents IA spécialisés pour générer, structurer et optimiser du code en fonction d'un prompt donné.

## Architecture

```
┌─────────────────┐       ┌──────────────────────┐
│   Interface CLI  │ <───> │    Agent Coordinateur │
└─────────────────┘       └──────────┬───────────┘
                                    │ (Orchestration)
      ┌───────────────────────┬─────┴─────┬───────────────────────┐
      │                       │           │                       │
┌──────▼──────┐        ┌───────▼──────┐    ┌───────▼──────┐        ┌───────▼──────┐
│  Analyseur   │        │ Générateur   │    │ Vérificateur │        │ Documenteur  │
│ (NLP/Intent) │        │  (CodeGen)   │    │ (Linter/Sec) │        │ (Comments)   │
└──────────────┘        └──────────────┘    └──────────────┘        └──────────────┘
```

## Fonctionnalités principales
✅ Génération de code Python à partir d'un prompt
✅ Validation syntaxique et stylistique du code généré
✅ Interface CLI interactive
✅ Communication asynchrone via Redis PubSub
✅ Architecture extensible prête pour l'ajout de nouvelles fonctionnalités

## Technologies utilisées
- **Langage** : Python 3.10+
- **Communication multi-agent** : Redis PubSub
- **Architecture** : Async/await pour la concurrence
- **Style de code** : PEP 8, Google Style Docstrings, Typing hints

## Prérequis

- Python 3.10+
- Redis server

## Installation

1. Cloner le dépôt :

```bash
git clone https://github.com/votre-utilisateur/multicoder.git
cd multicoder
```

2. Installer les dépendances :

```bash
pip install redis
```

3. Démarrer un serveur Redis (si non déjà en cours d'exécution) :

```bash
# Option 1: Utiliser Docker
docker run -d -p 6379:6379 redis

# Option 2: Installation locale
# Suivre les instructions sur https://redis.io/download
```

## Utilisation

### Démarrer tous les agents

```bash
python -m multicoder
```

### Démarrer des composants spécifiques

```bash
# Démarrer uniquement le coordinateur
python -m multicoder --component coordinator

# Démarrer uniquement le générateur de code
python -m multicoder --component generator

# Démarrer uniquement le validateur de code
python -m multicoder --component validator
```

### Utiliser l'interface CLI

```bash
python -m cli.multicoder
```

En mode interactif, tapez votre prompt de génération de code. Par exemple :

```
🔍 Enter your code request: Crée une fonction Python qui inverse une chaîne sans utiliser [::-1]
```

## Configuration

Les paramètres de configuration peuvent être modifiés via des variables d'environnement :

- `MULTICODER_REDIS_URL` : URL de connexion Redis (défaut : `redis://localhost:6379/0`)
- `MULTICODER_LOG_LEVEL` : Niveau de log (défaut : `INFO`)
- `MULTICODER_DEFAULT_TIMEOUT` : Timeout par défaut en secondes (défaut : `60`)

## Structure du projet

```
multicoder/
├── cli/                # Interface ligne de commande
├── config/             # Configuration
├── core/               # Logique principale
│   └── agents/         # Agents du système
├── db/                 # Couche d'accès aux données (Redis)
└── utils/              # Utilitaires
```

## Contribuer
Les contributions sont les bienvenues ! Clonez le repo, proposez des améliorations et ouvrez une pull request.

## Licence
MIT License © 2025 MultiCoder Team