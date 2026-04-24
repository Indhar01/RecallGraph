# MemoGraph CLI - PowerShell Examples
# Run these commands one at a time in PowerShell

# 1. Create a memory (single line)
python -m memograph --vault test_vault remember --title "Python Best Practices" --content "Always use type hints for better code clarity" --tags python,coding --salience 0.8

# 2. List all memories
python -m memograph --vault test_vault list

# 3. Search memories
python -m memograph --vault test_vault search "python type hints"

# 4. View statistics
python -m memograph --vault test_vault stats

# 5. Export to JSON
python -m memograph --vault test_vault export --output backup.json --format json

# 6. Create backup
python -m memograph --vault test_vault backup --destination backups

# 7. Batch create from JSON
python -m memograph --vault test_vault batch-create test_data/sample_memories.json --auto-ingest

# 8. Config commands
python -m memograph config set default_vault test_vault
python -m memograph config get default_vault
python -m memograph config list

Write-Host "`n=== MemoGraph CLI Examples ===" -ForegroundColor Green
Write-Host "Copy and paste individual commands above to try them out!" -ForegroundColor Yellow
Write-Host "`nFor full documentation, see: MEMOGRAPH_CLI_USAGE_GUIDE.md" -ForegroundColor Cyan
