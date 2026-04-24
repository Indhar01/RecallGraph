#!/bin/bash
# Example CLI workflow for MemoGraph

# Set vault path
VAULT="~/knowledge-vault"

# 1. Create some memories
memograph --vault $VAULT remember \
    --title "Project Setup" \
    --content "Initialized the project with Python 3.10 and FastAPI" \
    --type episodic \
    --tags project setup

memograph --vault $VAULT remember \
    --title "FastAPI Basics" \
    --content "FastAPI is a modern Python web framework with automatic API docs" \
    --type semantic \
    --tags fastapi python

# 2. Index the vault
memograph --vault $VAULT ingest

# 3. Query the vault
memograph --vault $VAULT context \
    --query "Tell me about the project setup" \
    --tags project \
    --top-k 5

# 4. Interactive chat (requires Ollama)
# memograph --vault $VAULT ask --chat --provider ollama --model llama3

# 5. Single question with Claude
# memograph --vault $VAULT ask \
#     --query "What framework are we using?" \
#     --provider claude \
#     --model claude-3-5-sonnet-20240620

# 6. Check system status
memograph --vault $VAULT doctor
