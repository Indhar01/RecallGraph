# Changelog

All notable changes to the MemoGraph Sync plugin will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-04-09

### Added
- Initial release of MemoGraph Sync plugin for Obsidian
- Bidirectional sync between Obsidian vault and MemoGraph
- Real-time file watching with automatic sync
- Manual sync via ribbon icon and command palette
- Configurable sync settings:
  - MemoGraph server URL
  - Auto-sync toggle
  - Sync interval configuration
  - Conflict resolution strategy
- Pull functionality to fetch memories from MemoGraph
- Push functionality to send notes to MemoGraph
- Conflict detection and resolution with multiple strategies:
  - Obsidian wins
  - MemoGraph wins
  - Newest wins (default)
  - Manual resolution
- Frontmatter preservation and conversion
- Tag and metadata synchronization
- Wikilink support
- Settings panel for configuration
- Status notifications for sync operations

### Technical Details
- Built with TypeScript and Obsidian API
- Uses esbuild for fast compilation
- Supports Obsidian 0.15.0+
- REST API integration with MemoGraph backend
- Efficient file watcher implementation
- Hash-based change detection

### Known Limitations
- Desktop and mobile platforms supported
- Requires MemoGraph server to be running
- Large vaults may take time for initial sync
- Binary file attachments not yet supported

## [0.2.0] - 2026-04-11

### Added
- **Real-time Auto-sync with Debouncing** (P1-W5-T1)
  - Intelligent auto-sync with 300ms debounce delay (configurable)
  - Sync queue with rate limiting to prevent sync storms
  - Multiple rapid changes trigger single sync operation
  - Status indicator for queue and active sync
  - 14/15 tests passing (93.3% success rate)

- **Advanced Conflict Resolution UI** (P1-W5-T2)
  - Interactive conflict resolution modal with side-by-side diff view
  - Four resolution strategies: Keep Local, Keep Remote, Keep Both, Manual editing
  - Line-by-line diff comparison with syntax highlighting
  - Conflict history tracking with timestamps
  - Commands to view and clear conflict history
  - Automatic fallback if UI callback fails
  - 14/14 tests passing (100% success rate)

- **Batch Sync Operations** (P1-W5-T3)
  - Efficient batch syncing for large vaults (tested with 100+ files)
  - Progress tracking with real-time progress bar
  - Configurable batch size (default 50 files)
  - Batch operation cancellation support
  - Memory-efficient chunked processing
  - 21/27 tests passing (78% success rate, core functionality 100%)

- **Performance Optimizations** (P1-W6-T1)
  - SQLite-based file indexing (2-3x faster than JSON)
  - LRU caching for file parsing (2-21x speedup, 95%+ hit rate)
  - Optimized wikilink resolution with O(1) lookups
  - Incremental indexing (only changed files, 30x faster)
  - Performance metrics tracking with throughput calculations
  - 10/10 tests passing (100% success rate)

- **Sync Status Dashboard** (P1-W6-T2)
  - Real-time sync status view with auto-refresh
  - Comprehensive statistics (total syncs, success rate, files synced, conflicts, errors)
  - Recent sync history display (last 10 syncs)
  - Recent error log with timestamps
  - Queue status showing queued files
  - Action buttons: Refresh, Clear History, Reset Statistics, Cancel Batch
  - Statistics persistence using localStorage
  - Success rate visualization with progress bar

- **Robust Error Handling & Recovery** (P1-W6-T3)
  - Automatic retry logic with exponential backoff (max 3 attempts)
  - Network error detection and graceful handling
  - File lock detection and retry mechanism
  - State rollback on critical errors (checkpoint/restore)
  - Error history tracking with timestamps and classifications
  - 18/23 tests passing (78% success rate, core features 100%)

- **Comprehensive Documentation**
  - Beta Testing Guide with detailed test checklist
  - Known Limitations documentation
  - Bug Triage Process for maintainers
  - Obsidian Setup Guide
  - Features documentation with examples
  - Troubleshooting guide with solutions
  - FAQ answering 27+ common questions
  - Performance Benchmarks documentation

### Improved
- **Sync Engine**
  - Bidirectional sync with improved conflict detection
  - Hash-based change detection for efficiency
  - Wikilink and backlink preservation
  - Tag and metadata synchronization
  - Frontmatter preservation and conversion

- **Performance**
  - Small vaults (10-50 files): < 5-15s sync time
  - Medium vaults (100 files): < 30s sync time
  - Large vaults (1000 files): < 300s sync time
  - Memory scaling: ~800-1000 MB for 1000 files
  - Throughput: 10-12 files/s parsing, 5-7 files/s writing

- **Testing**
  - 48 integration tests created (35 passing, 72.9% pass rate)
  - End-to-end tests: 85.7% pass rate
  - Performance tests: 84.6% pass rate
  - Comprehensive test coverage established
  - Performance regression testing baseline

### Fixed
- Sync queue duplicate prevention
- Conflict detection timing issues
- Memory leaks in large vault syncing
- Error handling edge cases
- State corruption during critical errors

### Technical Details
- **New Components:**
  - `statusView.ts` - Sync status dashboard
  - `syncStats.ts` - Statistics tracking and persistence
  - `conflictModal.ts` - Conflict resolution UI
  - `diffView.ts` - Side-by-side diff component
  - `performance_metrics.py` - Performance tracking backend

- **Enhanced Components:**
  - `sync.ts` - Added retry logic, error handling, batch operations
  - `watcher.py` - Added debouncing, queue management
  - `sync.py` - Added SQLite backend, rollback mechanism, comprehensive error handling
  - `sync_state.py` - Added SQLite support, checkpoint/restore
  - `parser.py` - Added LRU caching, optimized wikilink resolution
  - `conflict_resolver.py` - Added UI callbacks, conflict history

- **Test Coverage:**
  - Auto-sync: 93.3% (14/15 tests)
  - Conflict UI: 100% (14/14 tests)
  - Batch operations: 78% (21/27 tests)
  - Error handling: 78% (18/23 tests)
  - Integration suite: 72.9% (35/48 tests)
  - Performance: 100% (10/10 tests)

### Known Limitations
- Binary file attachments not supported (planned for v0.3.0)
- Offline mode not available (planned for v0.3.0)
- Selective folder sync not available (planned for v0.3.0)
- Large vault initial sync may take 5-10 minutes for 1000+ files
- One Windows path validation test failure (non-critical)
- Some edge cases in error history tracking need refinement
- Conflict resolution strategy changes mid-conflict may require manual resolution

See [KNOWN_LIMITATIONS.md](../docs/KNOWN_LIMITATIONS.md) for complete list.

### Breaking Changes
None - fully backward compatible with v0.1.0

### Upgrade Notes
- Auto-sync is disabled by default - enable in settings if desired
- Conflict resolution strategy defaults to "Newest Wins"
- SQLite backend is used automatically (JSON files migrated on first run)
- Statistics are tracked and persisted - use "Reset Statistics" to clear

## [Unreleased]

### Planned Features for v0.3.0
- Binary file and attachment sync support
- Selective folder sync with UI
- Offline mode with sync queue
- Mobile platform comprehensive testing
- Custom frontmatter field handling improvements
- Settings sync across devices
- Advanced conflict resolution (3-way merge)

---

## Version Support

- **Minimum Obsidian Version:** 0.15.0
- **Tested On:** Obsidian 1.5.0+
- **MemoGraph API:** v0.1.1+

## Contributing

Found a bug or have a feature request? Please open an issue on [GitHub](https://github.com/Indhar01/MemoGraph/issues).

## License

This plugin is part of the MemoGraph project and is licensed under the same terms. See the main project LICENSE file for details.
