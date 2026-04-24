"""Helper functions for CLI operations.

This module provides utility functions for file operations, memory management,
and other CLI-related tasks.
"""

import csv
import json
from pathlib import Path
from typing import Any

import yaml

from .core.kernel import MemoryKernel, SearchOptions


def find_memory_by_id(vault_path: Path, memory_id: str) -> Path | None:
    """Find memory file by ID in frontmatter.
    
    Args:
        vault_path: Path to vault directory
        memory_id: Memory ID to search for
        
    Returns:
        Path to memory file if found, None otherwise
    """
    for md_file in vault_path.rglob("*.md"):
        try:
            content = md_file.read_text(encoding="utf-8")
            # Check for ID in frontmatter (with or without quotes)
            if f"id: {memory_id}" in content or f'id: "{memory_id}"' in content:
                return md_file
        except Exception:
            continue
    return None


def read_memory_file(path: Path) -> dict[str, Any]:
    """Read and parse memory file with YAML frontmatter.
    
    Args:
        path: Path to memory file
        
    Returns:
        Dictionary with frontmatter fields and content
        
    Raises:
        ValueError: If file format is invalid
    """
    content = path.read_text(encoding="utf-8")
    
    # Parse frontmatter
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            frontmatter = yaml.safe_load(parts[1])
            body = parts[2].strip()
            
            # Extract tags from body content (format: #tag1,tag2 or #tag1 #tag2)
            tags = []
            for line in body.split('\n'):
                line = line.strip()
                if line.startswith('#'):
                    # Remove leading # and split by comma or space
                    tag_text = line.lstrip('#')
                    # Split by comma first, then by space
                    for tag_group in tag_text.split(','):
                        for tag in tag_group.split():
                            tag = tag.strip().lstrip('#')
                            if tag:
                                tags.append(tag)
            
            result = {
                **frontmatter,
                "content": body,
                "path": path
            }
            
            # Add tags if found
            if tags:
                result["tags"] = tags
            
            return result
    
    raise ValueError(f"Invalid memory file format: {path}")


def write_memory_file(path: Path, data: dict[str, Any]) -> None:
    """Write memory file with YAML frontmatter.
    
    Args:
        path: Path to memory file
        data: Dictionary with frontmatter fields and content
    """
    # Build frontmatter (exclude content, path, and tags)
    frontmatter_data = {
        k: v for k, v in data.items()
        if k not in ["content", "path", "tags"]
    }
    
    frontmatter = yaml.dump(frontmatter_data, default_flow_style=False, sort_keys=False)
    
    # Build body content
    body = data.get('content', '').strip()
    
    # Append tags to body if present
    tags = data.get('tags', [])
    if tags:
        tags_line = " ".join(f"#{tag}" for tag in tags)
        body = f"{body}\n\n{tags_line}"
    
    # Build file content
    content = f"---\n{frontmatter}---\n\n{body}\n"
    
    # Write file
    path.write_text(content, encoding="utf-8")


def find_memories_by_filter(
    vault_path: Path,
    tags: list[str] | None = None,
    memory_type: str | None = None,
    min_salience: float | None = None,
    max_salience: float | None = None
) -> list[dict[str, Any]]:
    """Find memories matching filter criteria.
    
    Args:
        vault_path: Path to vault directory
        tags: Filter by tags (any match)
        memory_type: Filter by memory type
        min_salience: Minimum salience threshold
        max_salience: Maximum salience threshold
        
    Returns:
        List of memory dictionaries matching filters
    """
    matches = []
    
    for md_file in vault_path.rglob("*.md"):
        try:
            memory = read_memory_file(md_file)
            
            # Apply filters
            if tags and not any(t in memory.get('tags', []) for t in tags):
                continue
            
            if memory_type and memory.get('memory_type') != memory_type:
                continue
            
            salience = memory.get('salience', 0.0)
            if min_salience is not None and salience < min_salience:
                continue
            
            if max_salience is not None and salience > max_salience:
                continue
            
            matches.append(memory)
            
        except Exception:
            continue
    
    return matches


def update_single_memory(kernel: MemoryKernel, vault_path: Path, args) -> None:
    """Update a single memory by ID.
    
    Args:
        kernel: MemoryKernel instance
        vault_path: Path to vault directory
        args: Parsed command-line arguments
    """
    # Find memory file
    memory_path = find_memory_by_id(vault_path, args.memory_id)
    if not memory_path:
        print(f"Error: Memory '{args.memory_id}' not found")
        return
    
    # Read current content
    try:
        current = read_memory_file(memory_path)
    except Exception as e:
        print(f"Error reading memory: {e}")
        return
    
    # Show current state
    print(f"\n=== Current Memory ===")
    print(f"ID: {args.memory_id}")
    print(f"Title: {current.get('title', 'N/A')}")
    print(f"Type: {current.get('memory_type', 'N/A')}")
    print(f"Salience: {current.get('salience', 0.0)}")
    print(f"Tags: {', '.join(current.get('tags', []))}")
    
    # Build updates
    updates = {}
    if args.title:
        updates['title'] = args.title
    if args.content:
        updates['content'] = args.content
    if args.type:
        updates['memory_type'] = args.type
    if args.salience is not None:
        updates['salience'] = args.salience
    
    # Handle tags
    if args.set_tags is not None:
        updates['tags'] = args.set_tags
    elif args.add_tags or args.remove_tags:
        new_tags = set(current.get('tags', []))
        if args.add_tags:
            new_tags.update(args.add_tags)
        if args.remove_tags:
            new_tags.difference_update(args.remove_tags)
        updates['tags'] = list(new_tags)
    
    # Show proposed changes
    print(f"\n=== Proposed Changes ===")
    for key, value in updates.items():
        old_value = current.get(key, 'N/A')
        if key == 'content':
            # Truncate content for display
            old_preview = str(old_value)[:50] + "..." if len(str(old_value)) > 50 else old_value
            new_preview = str(value)[:50] + "..." if len(str(value)) > 50 else value
            print(f"{key}: {old_preview} → {new_preview}")
        else:
            print(f"{key}: {old_value} → {value}")
    
    # Dry run check
    if args.dry_run:
        print("\n[DRY RUN] No changes applied")
        return
    
    # Confirmation
    if not args.confirm:
        response = input("\nApply changes? (y/N): ")
        if response.lower() != 'y':
            print("Update cancelled")
            return
    
    # Apply updates
    try:
        updated_data = {**current, **updates}
        write_memory_file(memory_path, updated_data)
        print(f"\n[OK] Updated memory: {args.memory_id}")
        
        # Re-ingest to update graph
        print("Updating graph...")
        kernel.ingest(force=False)
        print("[OK] Graph updated")
        
    except Exception as e:
        print(f"\n[ERROR] Update failed: {e}")


def update_filtered_memories(kernel: MemoryKernel, vault_path: Path, args) -> None:
    """Update multiple memories using filters.
    
    Args:
        kernel: MemoryKernel instance
        vault_path: Path to vault directory
        args: Parsed command-line arguments
    """
    # Find matching memories
    matches = find_memories_by_filter(
        vault_path,
        tags=args.filter_tags,
        memory_type=args.filter_type,
        min_salience=args.filter_min_salience,
        max_salience=args.filter_max_salience
    )
    
    if not matches:
        print("No memories match the filter criteria")
        return
    
    print(f"\n=== Found {len(matches)} matching memories ===")
    for i, m in enumerate(matches[:10], 1):  # Show first 10
        print(f"{i}. {m.get('id', 'N/A')}: {m.get('title', 'Untitled')}")
    
    if len(matches) > 10:
        print(f"... and {len(matches) - 10} more")
    
    # Build updates
    updates = {}
    if args.title:
        updates['title'] = args.title
    if args.content:
        updates['content'] = args.content
    if args.type:
        updates['memory_type'] = args.type
    if args.salience is not None:
        updates['salience'] = args.salience
    
    # Handle tags for bulk update
    if args.set_tags is not None:
        updates['tags'] = args.set_tags
    
    print(f"\n=== Updates to apply ===")
    for key, value in updates.items():
        if key == 'content':
            preview = str(value)[:50] + "..." if len(str(value)) > 50 else value
            print(f"{key}: {preview}")
        else:
            print(f"{key}: {value}")
    
    # Tag operations for bulk
    if args.add_tags:
        print(f"Add tags: {', '.join(args.add_tags)}")
    if args.remove_tags:
        print(f"Remove tags: {', '.join(args.remove_tags)}")
    
    # Dry run check
    if args.dry_run:
        print("\n[DRY RUN] No changes applied")
        return
    
    # Confirmation
    if not args.confirm:
        response = input(f"\nUpdate {len(matches)} memories? (y/N): ")
        if response.lower() != 'y':
            print("Update cancelled")
            return
    
    # Apply updates
    success_count = 0
    error_count = 0
    
    for memory in matches:
        try:
            # Apply field updates
            updated_data = {**memory, **updates}
            
            # Apply tag operations
            if args.add_tags or args.remove_tags:
                current_tags = set(memory.get('tags', []))
                if args.add_tags:
                    current_tags.update(args.add_tags)
                if args.remove_tags:
                    current_tags.difference_update(args.remove_tags)
                updated_data['tags'] = list(current_tags)
            
            write_memory_file(memory['path'], updated_data)
            success_count += 1
        except Exception as e:
            print(f"[ERROR] Failed to update {memory.get('id', 'unknown')}: {e}")
            error_count += 1
    
    print(f"\n=== Update Summary ===")
    print(f"[OK] Success: {success_count}")
    print(f"[ERROR] Failed: {error_count}")
    
    # Re-ingest
    if success_count > 0:
        print("\nUpdating graph...")
        kernel.ingest(force=False)
        print("[OK] Graph updated")


def run_update_command(kernel: MemoryKernel, args) -> None:
    """Handle update command for modifying memories.
    
    Args:
        kernel: MemoryKernel instance
        args: Parsed command-line arguments
    """
    vault_path = Path(kernel.vault_path)
    
    # Validate at least one update field is provided
    update_fields = {
        "title": args.title,
        "content": args.content,
        "memory_type": args.type,
        "salience": args.salience,
    }
    
    has_update = any(update_fields.values()) or any([
        args.add_tags, args.remove_tags, args.set_tags
    ])
    
    if not has_update:
        print("Error: At least one update field must be specified")
        print("Use --title, --content, --type, --salience, or tag options")
        return
    
    # Single memory update
    if args.memory_id:
        update_single_memory(kernel, vault_path, args)
    
    # Bulk update with filters
    elif args.filter:
        update_filtered_memories(kernel, vault_path, args)


def delete_single_memory(kernel: MemoryKernel, vault_path: Path, args) -> None:
    """Delete a single memory by ID.
    
    Args:
        kernel: MemoryKernel instance
        vault_path: Path to vault directory
        args: Parsed command-line arguments
    """
    # Find memory file
    memory_path = find_memory_by_id(vault_path, args.memory_id)
    if not memory_path:
        print(f"Error: Memory '{args.memory_id}' not found")
        return
    
    # Read current content for display
    try:
        current = read_memory_file(memory_path)
    except Exception as e:
        print(f"Error reading memory: {e}")
        return
    
    # Show memory to be deleted
    print(f"\n=== Memory to Delete ===")
    print(f"ID: {args.memory_id}")
    print(f"Title: {current.get('title', 'N/A')}")
    print(f"Type: {current.get('memory_type', 'N/A')}")
    print(f"File: {memory_path}")
    
    # Dry run check
    if args.dry_run:
        print("\n[DRY RUN] No files deleted")
        return
    
    # Confirmation
    if not args.confirm:
        response = input("\n[WARNING]  Delete this memory? This cannot be undone! (y/N): ")
        if response.lower() != 'y':
            print("Deletion cancelled")
            return
    
    # Delete file
    try:
        memory_path.unlink()
        print(f"\n[OK] Deleted memory: {args.memory_id}")
        
        # Re-ingest to update graph
        print("Updating graph...")
        kernel.ingest(force=False)
        print("[OK] Graph updated")
        
    except Exception as e:
        print(f"\n[ERROR] Deletion failed: {e}")


def delete_filtered_memories(kernel: MemoryKernel, vault_path: Path, args) -> None:
    """Delete multiple memories using filters.
    
    Args:
        kernel: MemoryKernel instance
        vault_path: Path to vault directory
        args: Parsed command-line arguments
    """
    # Find matching memories
    matches = find_memories_by_filter(
        vault_path,
        tags=args.filter_tags,
        memory_type=args.filter_type,
        min_salience=args.filter_min_salience,
        max_salience=args.filter_max_salience
    )
    
    if not matches:
        print("No memories match the filter criteria")
        return
    
    print(f"\n=== Found {len(matches)} matching memories ===")
    for i, m in enumerate(matches[:10], 1):  # Show first 10
        print(f"{i}. {m.get('id', 'N/A')}: {m.get('title', 'Untitled')}")
    
    if len(matches) > 10:
        print(f"... and {len(matches) - 10} more")
    
    # Dry run check
    if args.dry_run:
        print("\n[DRY RUN] No files deleted")
        return
    
    # Confirmation
    if not args.confirm:
        response = input(f"\n[WARNING]  Delete {len(matches)} memories? This cannot be undone! (y/N): ")
        if response.lower() != 'y':
            print("Deletion cancelled")
            return
    
    # Delete files
    success_count = 0
    error_count = 0
    
    for memory in matches:
        try:
            memory['path'].unlink()
            success_count += 1
        except Exception as e:
            print(f"[ERROR] Failed to delete {memory.get('id', 'unknown')}: {e}")
            error_count += 1
    
    print(f"\n=== Deletion Summary ===")
    print(f"[OK] Deleted: {success_count}")
    print(f"[ERROR] Failed: {error_count}")
    
    # Re-ingest
    if success_count > 0:
        print("\nUpdating graph...")
        kernel.ingest(force=False)
        print("[OK] Graph updated")


def run_delete_command(kernel: MemoryKernel, args) -> None:
    """Handle delete command for removing memories.
    
    Args:
        kernel: MemoryKernel instance
        args: Parsed command-line arguments
    """
    vault_path = Path(kernel.vault_path)
    
    # Single memory deletion
    if args.memory_id:
        delete_single_memory(kernel, vault_path, args)
    
    # Bulk deletion with filters
    elif args.filter:
        delete_filtered_memories(kernel, vault_path, args)


def find_all_memories(vault_path: Path) -> list[dict[str, Any]]:
    """Find all memories in vault.
    
    Args:
        vault_path: Path to vault directory
        
    Returns:
        List of all memory dictionaries
    """
    memories = []
    
    for md_file in vault_path.rglob("*.md"):
        try:
            memory = read_memory_file(md_file)
            memories.append(memory)
        except Exception:
            continue
    
    return memories


def sort_memories(memories: list[dict[str, Any]], sort_by: str, reverse: bool = False) -> list[dict[str, Any]]:
    """Sort memories by specified field.
    
    Args:
        memories: List of memory dictionaries
        sort_by: Field to sort by (title, salience, type, created, modified)
        reverse: Sort in descending order if True
        
    Returns:
        Sorted list of memories
    """
    def get_sort_key(memory: dict[str, Any]) -> Any:
        if sort_by == "title":
            return memory.get('title', '').lower()
        elif sort_by == "salience":
            return memory.get('salience', 0.0)
        elif sort_by == "type":
            return memory.get('memory_type', '')
        elif sort_by == "created":
            return memory.get('created_at', '')
        elif sort_by == "modified":
            # Use file modification time
            path = memory.get('path')
            if path and isinstance(path, Path):
                return path.stat().st_mtime
            return 0
        return ''
    
    return sorted(memories, key=get_sort_key, reverse=reverse)


def format_table_output(memories: list[dict[str, Any]]) -> str:
    """Format memories as a table.
    
    Args:
        memories: List of memory dictionaries
        
    Returns:
        Formatted table string
    """
    if not memories:
        return "No memories found."
    
    # Calculate column widths
    id_width = max(len(m.get('id', '')) for m in memories) if memories else 10
    id_width = max(id_width, 10)  # Minimum width
    
    title_width = max(len(m.get('title', '')) for m in memories) if memories else 20
    title_width = min(max(title_width, 20), 50)  # Between 20-50 chars
    
    type_width = 12
    salience_width = 8
    tags_width = 30
    
    # Build header
    header = f"{'ID':<{id_width}} | {'Title':<{title_width}} | {'Type':<{type_width}} | {'Salience':<{salience_width}} | {'Tags':<{tags_width}}"
    separator = "-" * len(header)
    
    lines = [header, separator]
    
    # Build rows
    for memory in memories:
        mem_id = memory.get('id', 'N/A')[:id_width]
        title = memory.get('title', 'Untitled')[:title_width]
        mem_type = memory.get('memory_type', 'N/A')[:type_width]
        salience = f"{memory.get('salience', 0.0):.2f}"
        tags = ', '.join(memory.get('tags', []))[:tags_width]
        
        row = f"{mem_id:<{id_width}} | {title:<{title_width}} | {mem_type:<{type_width}} | {salience:<{salience_width}} | {tags:<{tags_width}}"
        lines.append(row)
    
    return '\n'.join(lines)


def format_json_output(memories: list[dict[str, Any]]) -> str:
    """Format memories as JSON.
    
    Args:
        memories: List of memory dictionaries
        
    Returns:
        JSON string
    """
    from datetime import datetime
    
    # Remove path objects and convert datetime for JSON serialization
    clean_memories = []
    for memory in memories:
        clean_mem = {}
        for k, v in memory.items():
            if k == 'path':
                continue
            # Convert datetime objects to ISO format strings
            if isinstance(v, datetime):
                clean_mem[k] = v.isoformat()
            else:
                clean_mem[k] = v
        clean_memories.append(clean_mem)
    
    return json.dumps(clean_memories, indent=2, ensure_ascii=False)


def format_csv_output(memories: list[dict[str, Any]]) -> str:
    """Format memories as CSV.
    
    Args:
        memories: List of memory dictionaries
        
    Returns:
        CSV string
    """
    if not memories:
        return ""
    
    # Determine all fields
    fields = ['id', 'title', 'memory_type', 'salience', 'tags', 'created_at']
    
    # Build CSV
    output = []
    output.append(','.join(fields))
    
    for memory in memories:
        row = []
        for field in fields:
            value = memory.get(field, '')
            if field == 'tags' and isinstance(value, list):
                value = ';'.join(value)
            row.append(f'"{value}"')
        output.append(','.join(row))
    
    return '\n'.join(output)


def format_ids_output(memories: list[dict[str, Any]]) -> str:
    """Format memories as ID list only.
    
    Args:
        memories: List of memory dictionaries
        
    Returns:
        Newline-separated IDs
    """
    return '\n'.join(m.get('id', '') for m in memories if m.get('id'))


def run_list_command(kernel: MemoryKernel, args) -> None:
    """Handle list command for displaying memories.
    
    Args:
        kernel: MemoryKernel instance
        args: Parsed command-line arguments
    """
    vault_path = Path(kernel.vault_path)
    
    # Find memories
    if args.tags or args.type or args.min_salience or args.max_salience:
        memories = find_memories_by_filter(
            vault_path,
            tags=args.tags,
            memory_type=args.type,
            min_salience=args.min_salience,
            max_salience=args.max_salience
        )
    else:
        memories = find_all_memories(vault_path)
    
    if not memories:
        print("No memories found.")
        return
    
    # Sort memories
    if args.sort_by:
        memories = sort_memories(memories, args.sort_by, args.reverse)
    
    # Apply pagination
    if args.limit:
        offset = args.offset or 0
        memories = memories[offset:offset + args.limit]
    
    # Format output
    if args.format == 'table':
        output = format_table_output(memories)
    elif args.format == 'json':
        output = format_json_output(memories)
    elif args.format == 'csv':
        output = format_csv_output(memories)
    elif args.format == 'ids':
        output = format_ids_output(memories)
    else:
        output = format_table_output(memories)
    
    print(output)



def format_search_table(results: list, show_scores: bool = False, show_snippets: bool = False) -> str:
    """Format search results as a table.
    
    Args:
        results: List of MemoryNode objects
        show_scores: Whether to show relevance scores
        show_snippets: Whether to show content snippets
        
    Returns:
        Formatted table string
    """
    if not results:
        return "No results found."
    
    # Calculate column widths
    id_width = max(len(getattr(r, 'id', '')) for r in results) if results else 10
    id_width = max(id_width, 10)
    
    title_width = max(len(getattr(r, 'title', '')) for r in results) if results else 30
    title_width = min(max(title_width, 30), 60)
    
    type_width = 12
    salience_width = 8
    score_width = 8 if show_scores else 0
    
    # Build header
    header_parts = [
        f"{'ID':<{id_width}}",
        f"{'Title':<{title_width}}",
        f"{'Type':<{type_width}}",
        f"{'Salience':<{salience_width}}"
    ]
    
    if show_scores:
        header_parts.append(f"{'Score':<{score_width}}")
    
    header = " | ".join(header_parts)
    separator = "-" * len(header)
    
    lines = [header, separator]
    
    # Build rows
    for result in results:
        node_id = getattr(result, 'id', 'N/A')[:id_width]
        title = getattr(result, 'title', 'Untitled')[:title_width]
        mem_type = getattr(result, 'memory_type', 'N/A')
        node_type = str(mem_type)[:type_width] if mem_type != 'N/A' else 'N/A'
        salience = f"{getattr(result, 'salience', 0.0):.2f}"
        
        row_parts = [
            f"{node_id:<{id_width}}",
            f"{title:<{title_width}}",
            f"{node_type:<{type_width}}",
            f"{salience:<{salience_width}}"
        ]
        
        if show_scores:
            score = getattr(result, 'score', 0.0)
            row_parts.append(f"{score:<{score_width}.2f}")
        
        lines.append(" | ".join(row_parts))
        
        # Add snippet if requested
        if show_snippets:
            content = getattr(result, 'content', '')
            snippet = content[:100] + "..." if len(content) > 100 else content
            lines.append(f"  → {snippet}")
            lines.append("")
    
    return '\n'.join(lines)


def format_search_json(results: list) -> str:
    """Format search results as JSON.
    
    Args:
        results: List of MemoryNode objects
        
    Returns:
        JSON string
    """
    from datetime import datetime
    
    result_list = []
    for result in results:
        mem_type = getattr(result, 'memory_type', None)
        result_dict = {
            'id': getattr(result, 'id', None),
            'title': getattr(result, 'title', None),
            'content': getattr(result, 'content', None),
            'memory_type': str(mem_type) if mem_type is not None else None,
            'salience': getattr(result, 'salience', None),
            'tags': getattr(result, 'tags', []),
            'score': getattr(result, 'score', None),
            'created_at': getattr(result, 'created_at', None),
        }
        
        # Convert datetime to ISO format
        if isinstance(result_dict.get('created_at'), datetime):
            result_dict['created_at'] = result_dict['created_at'].isoformat()
        
        result_list.append(result_dict)
    
    return json.dumps(result_list, indent=2, ensure_ascii=False)


def format_search_detailed(results: list) -> str:
    """Format search results with detailed information.
    
    Args:
        results: List of MemoryNode objects
        
    Returns:
        Detailed formatted string
    """
    if not results:
        return "No results found."
    
    lines = []
    for i, result in enumerate(results, 1):
        lines.append(f"\n{'='*80}")
        lines.append(f"Result {i}/{len(results)}")
        lines.append(f"{'='*80}")
        mem_type = getattr(result, 'memory_type', 'N/A')
        lines.append(f"ID: {getattr(result, 'id', 'N/A')}")
        lines.append(f"Title: {getattr(result, 'title', 'Untitled')}")
        lines.append(f"Type: {str(mem_type) if mem_type != 'N/A' else 'N/A'}")
        lines.append(f"Salience: {getattr(result, 'salience', 0.0):.2f}")
        
        score = getattr(result, 'score', None)
        if score is not None:
            lines.append(f"Relevance Score: {score:.2f}")
        
        tags = getattr(result, 'tags', [])
        if tags:
            lines.append(f"Tags: {', '.join(tags)}")
        
        # Show content preview
        content = getattr(result, 'content', '')
        if content:
            lines.append(f"\nContent Preview:")
            preview = content[:300] + "..." if len(content) > 300 else content
            lines.append(preview)
        
        # Show connections if available
        connections = getattr(result, 'connections', [])
        if connections:
            lines.append(f"\nConnections: {len(connections)} related memories")
    
    return '\n'.join(lines)


def run_search_command(kernel: MemoryKernel, args) -> None:
    """Handle search command for finding memories.
    
    Args:
        kernel: MemoryKernel instance
        args: Parsed command-line arguments
    """
    # Build search options
    options = SearchOptions(
        strategy=args.strategy,
        min_salience=args.min_salience if args.min_salience is not None else 0.0,
        max_results=args.limit,
        depth=args.depth,
        boost_recent=args.boost_recent
    )
    
    # Set custom weights if provided
    if args.keyword_weight is not None or args.semantic_weight is not None:
        kw_weight = args.keyword_weight if args.keyword_weight is not None else 0.4
        sem_weight = args.semantic_weight if args.semantic_weight is not None else 0.6
        
        # Normalize weights to sum to 1.0
        total = kw_weight + sem_weight
        if total > 0:
            options.weights = {
                "keyword": kw_weight / total,
                "semantic": sem_weight / total
            }
    
    # Perform search
    try:
        results = kernel.search(args.query, options=options)
    except Exception as e:
        print(f"Search failed: {e}")
        return
    
    if not results:
        print("No results found.")
        return
    
    # Format output
    if args.format == 'table':
        output = format_search_table(results, args.show_scores, args.show_snippets)
    elif args.format == 'json':
        output = format_search_json(results)
    elif args.format == 'detailed':
        output = format_search_detailed(results)
    else:
        output = format_search_table(results, args.show_scores, args.show_snippets)
    
    print(output)
    
    # Show summary
    if args.format != 'json':
        print(f"\nFound {len(results)} results using {args.strategy} search")
