"""Batch operation helpers for CLI commands.

This module provides batch operation functions for creating, updating,
and deleting multiple memories efficiently.
"""

import csv
import json
from pathlib import Path
from typing import Any

from .core.enums import MemoryType
from .core.kernel import MemoryKernel


def run_batch_create_command(kernel: MemoryKernel, args) -> None:
    """Handle batch-create command for bulk memory creation.
    
    Args:
        kernel: MemoryKernel instance
        args: Parsed command-line arguments
    """
    input_path = Path(args.input_file)
    
    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}")
        return
    
    # Auto-detect format if not specified
    file_format = args.format
    if not file_format:
        if input_path.suffix.lower() == '.json':
            file_format = 'json'
        elif input_path.suffix.lower() == '.csv':
            file_format = 'csv'
        else:
            print(f"Error: Cannot detect format for {input_path.suffix}. Use --format")
            return
    
    # Load memories from file
    try:
        if file_format == 'json':
            memories = _load_memories_from_json(input_path)
        else:
            memories = _load_memories_from_csv(input_path)
    except Exception as e:
        print(f"Error loading file: {e}")
        return
    
    if not memories:
        print("No memories found in input file")
        return
    
    print(f"\n=== Batch Create: {len(memories)} memories ===")
    
    # Show preview
    for i, mem in enumerate(memories[:5], 1):
        print(f"{i}. {mem.get('title', 'Untitled')} ({mem.get('memory_type', 'fact')})")
    
    if len(memories) > 5:
        print(f"... and {len(memories) - 5} more")
    
    # Dry run check
    if args.dry_run:
        print("\n[DRY RUN] No memories created")
        return
    
    # Create memories with progress
    print("\nCreating memories...")
    success_count = 0
    error_count = 0
    errors = []
    
    try:
        # Try to use tqdm if available
        from tqdm import tqdm
        iterator = tqdm(memories, desc="Creating", unit="memory")
    except ImportError:
        iterator = memories
        print("(Install tqdm for progress bars: pip install tqdm)")
    
    for memory in iterator:
        try:
            kernel.remember(
                title=memory.get('title', 'Untitled'),
                content=memory.get('content', ''),
                memory_type=MemoryType(memory.get('memory_type', 'fact')),
                tags=memory.get('tags', []),
                salience=memory.get('salience', 0.5)
            )
            success_count += 1
        except Exception as e:
            error_count += 1
            errors.append(f"{memory.get('title', 'Unknown')}: {str(e)}")
    
    # Summary
    print(f"\n=== Batch Create Summary ===")
    print(f"[OK] Created: {success_count}")
    print(f"[ERROR] Failed: {error_count}")
    
    if errors and error_count <= 10:
        print("\nErrors:")
        for error in errors:
            print(f"  - {error}")
    
    # Auto-ingest if requested
    if args.auto_ingest and success_count > 0:
        print("\nRunning ingest...")
        stats = kernel.ingest()
        print(f"[OK] Indexed {stats['indexed']} files")


def run_batch_update_command(kernel: MemoryKernel, args) -> None:
    """Handle batch-update command for bulk memory updates.
    
    Args:
        kernel: MemoryKernel instance
        args: Parsed command-line arguments
    """
    from .cli_helpers import find_memories_by_filter, write_memory_file
    
    vault_path = Path(kernel.vault_path)
    
    # Determine update source
    if args.input_file:
        # File-based updates
        input_path = Path(args.input_file)
        if not input_path.exists():
            print(f"Error: Input file not found: {input_path}")
            return
        
        try:
            if input_path.suffix.lower() == '.json':
                updates = json.loads(input_path.read_text(encoding='utf-8'))
            else:
                print(f"Error: Unsupported file format: {input_path.suffix}")
                return
        except Exception as e:
            print(f"Error loading file: {e}")
            return
        
        print(f"\n=== Batch Update: {len(updates)} memories from file ===")
        
    else:
        # Filter-based updates
        matches = find_memories_by_filter(
            vault_path,
            tags=args.filter_tags,
            memory_type=args.filter_type
        )
        
        if not matches:
            print("No memories match the filter criteria")
            return
        
        print(f"\n=== Batch Update: {len(matches)} memories by filter ===")
        
        # Build update dict
        updates = []
        for match in matches:
            update = {'id': match.get('id')}
            if args.set_salience is not None:
                update['salience'] = args.set_salience
            if args.add_tags:
                current_tags = set(match.get('tags', []))
                current_tags.update(args.add_tags)
                update['tags'] = list(current_tags)
            updates.append(update)
    
    # Show preview
    for i, upd in enumerate(updates[:10], 1):
        print(f"{i}. {upd.get('id', 'Unknown')}")
    
    if len(updates) > 10:
        print(f"... and {len(updates) - 10} more")
    
    # Dry run check
    if args.dry_run:
        print("\n[DRY RUN] No updates applied")
        return
    
    # Confirmation
    if not args.confirm:
        response = input(f"\nUpdate {len(updates)} memories? (y/N): ")
        if response.lower() != 'y':
            print("Update cancelled")
            return
    
    # Apply updates with progress
    print("\nUpdating memories...")
    success_count = 0
    error_count = 0
    
    try:
        from tqdm import tqdm
        iterator = tqdm(updates, desc="Updating", unit="memory")
    except ImportError:
        iterator = updates
    
    for update in iterator:
        try:
            from .cli_helpers import find_memory_by_id, read_memory_file
            
            memory_path = find_memory_by_id(vault_path, update['id'])
            if not memory_path:
                error_count += 1
                continue
            
            current = read_memory_file(memory_path)
            updated_data = {**current, **update}
            write_memory_file(memory_path, updated_data)
            success_count += 1
        except Exception:
            error_count += 1
    
    print(f"\n=== Batch Update Summary ===")
    print(f"[OK] Updated: {success_count}")
    print(f"[ERROR] Failed: {error_count}")
    
    if success_count > 0:
        print("\nUpdating graph...")
        kernel.ingest(force=False)
        print("[OK] Graph updated")


def run_batch_delete_command(kernel: MemoryKernel, args) -> None:
    """Handle batch-delete command for bulk memory deletion.
    
    Args:
        kernel: MemoryKernel instance
        args: Parsed command-line arguments
    """
    from .cli_helpers import find_memories_by_filter
    
    vault_path = Path(kernel.vault_path)
    
    # Determine deletion targets
    if args.input_file:
        # File-based deletion
        input_path = Path(args.input_file)
        if not input_path.exists():
            print(f"Error: Input file not found: {input_path}")
            return
        
        try:
            memory_ids = input_path.read_text(encoding='utf-8').strip().split('\n')
            memory_ids = [mid.strip() for mid in memory_ids if mid.strip()]
        except Exception as e:
            print(f"Error loading file: {e}")
            return
        
        print(f"\n=== Batch Delete: {len(memory_ids)} memories from file ===")
        
        # Find memory paths
        from .cli_helpers import find_memory_by_id
        targets = []
        for mid in memory_ids:
            path = find_memory_by_id(vault_path, mid)
            if path:
                targets.append({'id': mid, 'path': path})
        
    else:
        # Filter-based deletion
        matches = find_memories_by_filter(
            vault_path,
            tags=args.filter_tags,
            memory_type=args.filter_type
        )
        
        if not matches:
            print("No memories match the filter criteria")
            return
        
        targets = matches
        print(f"\n=== Batch Delete: {len(targets)} memories by filter ===")
    
    # Show preview
    for i, target in enumerate(targets[:10], 1):
        print(f"{i}. {target.get('id', 'Unknown')}")
    
    if len(targets) > 10:
        print(f"... and {len(targets) - 10} more")
    
    # Dry run check
    if args.dry_run:
        print("\n[DRY RUN] No files deleted")
        return
    
    # Confirmation
    if not args.confirm:
        response = input(f"\n[WARNING]  Delete {len(targets)} memories? This cannot be undone! (y/N): ")
        if response.lower() != 'y':
            print("Deletion cancelled")
            return
    
    # Delete with progress
    print("\nDeleting memories...")
    success_count = 0
    error_count = 0
    
    try:
        from tqdm import tqdm
        iterator = tqdm(targets, desc="Deleting", unit="memory")
    except ImportError:
        iterator = targets
    
    for target in iterator:
        try:
            target['path'].unlink()
            success_count += 1
        except Exception:
            error_count += 1
    
    print(f"\n=== Batch Delete Summary ===")
    print(f"[OK] Deleted: {success_count}")
    print(f"[ERROR] Failed: {error_count}")
    
    if success_count > 0:
        print("\nUpdating graph...")
        kernel.ingest(force=False)
        print("[OK] Graph updated")


def _load_memories_from_json(path: Path) -> list[dict[str, Any]]:
    """Load memories from JSON file."""
    content = path.read_text(encoding='utf-8')
    data = json.loads(content)
    
    if isinstance(data, list):
        return data
    elif isinstance(data, dict) and 'memories' in data:
        return data['memories']
    else:
        raise ValueError("JSON must be a list or dict with 'memories' key")


def _load_memories_from_csv(path: Path) -> list[dict[str, Any]]:
    """Load memories from CSV file."""
    memories = []
    
    with open(path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Convert tags from semicolon-separated string
            if 'tags' in row and row['tags']:
                row['tags'] = [t.strip() for t in row['tags'].split(';')]
            else:
                row['tags'] = []
            
            # Convert salience to float
            if 'salience' in row:
                try:
                    row['salience'] = float(row['salience'])
                except (ValueError, TypeError):
                    row['salience'] = 0.5
            
            memories.append(row)
    
    return memories
