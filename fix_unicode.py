"""Fix Unicode characters in CLI helper files for Windows compatibility."""

import re
from pathlib import Path

# Unicode to ASCII mapping
REPLACEMENTS = {
    '✓': '[OK]',
    '✗': '[ERROR]',
    '⊘': '[SKIP]',
    '⚠️': '[WARNING]',
    '⚠': '[WARNING]',
}

def fix_file(filepath):
    """Replace Unicode characters in a file."""
    content = filepath.read_text(encoding='utf-8')
    original = content
    
    for unicode_char, ascii_replacement in REPLACEMENTS.items():
        content = content.replace(unicode_char, ascii_replacement)
    
    if content != original:
        filepath.write_text(content, encoding='utf-8')
        print(f"✓ Fixed: {filepath.name}")
        return True
    else:
        print(f"- No changes: {filepath.name}")
        return False

def main():
    """Fix all CLI helper files."""
    files = [
        Path('memograph/cli_batch_helpers.py'),
        Path('memograph/cli_infrastructure_helpers.py'),
        Path('memograph/cli_helpers.py'),
    ]
    
    fixed_count = 0
    for filepath in files:
        if filepath.exists():
            if fix_file(filepath):
                fixed_count += 1
        else:
            print(f"✗ Not found: {filepath}")
    
    print(f"\nFixed {fixed_count} file(s)")

if __name__ == '__main__':
    main()
