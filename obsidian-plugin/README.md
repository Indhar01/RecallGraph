# MemoGraph Sync - Obsidian Plugin

**Version:** 0.2.0
**Last Updated:** 2026-04-11
**Status:** Production Ready

Seamlessly synchronize your Obsidian vault with MemoGraph for AI-powered knowledge management, semantic search, and intelligent memory organization.

---

## ✨ Features

### Core Sync Features
- **🔄 Bidirectional Sync** - Keep Obsidian and MemoGraph perfectly in sync
- **⚡ Auto-Sync with Debouncing** - Intelligent real-time sync (300ms default)
- **📦 Batch Sync** - Efficiently sync 50-100 files at once with progress tracking
- **🔍 Incremental Sync** - Only sync changed files (30x faster for daily workflows)
- **🎯 Smart Filtering** - Sync by tags, folders, or custom patterns

### Conflict Resolution
- **🤝 Conflict Detection** - Automatic detection of sync conflicts
- **🎨 Visual Diff View** - Side-by-side comparison with syntax highlighting
- **4 Resolution Strategies** - Newest Wins (default), Obsidian Wins, MemoGraph Wins, Manual
- **📜 Conflict History** - Track and review past conflicts
- **💾 Keep Both Option** - Create separate files with timestamps

### Performance & Reliability
- **🚀 SQLite Backend** - 2-3x faster than JSON for large vaults
- **💨 LRU Caching** - 21x speedup on cached operations (95%+ hit rate)
- **🔗 Optimized Wikilinks** - O(1) lookup, case-insensitive, 100x faster resolution
- **🔁 Retry Logic** - Automatic retry with exponential backoff
- **♻️ Rollback Support** - State rollback on critical errors

### User Interface
- **📊 Status Dashboard** - Real-time sync statistics and history
- **🎚️ Progress Tracking** - Visual progress bars for batch operations
- **📈 Performance Metrics** - Files/sec, throughput, cache stats
- **🎗️ Ribbon Icon** - Quick access sync button
- **⌨️ Keyboard Shortcuts** - Customizable hotkeys for common actions

---

## 📖 Documentation

### For Users
- **[Setup Guide](../docs/OBSIDIAN_SETUP_GUIDE.md)** - Complete installation and configuration (10 minutes)
- **[Features Guide](../docs/OBSIDIAN_FEATURES.md)** - Detailed feature documentation with examples
- **[Troubleshooting](../docs/TROUBLESHOOTING.md)** - Solutions to common problems
- **[FAQ](../docs/OBSIDIAN_FAQ.md)** - Frequently asked questions (27+ questions answered)

### For Developers
- **[Performance Benchmarks](../docs/PERFORMANCE_BENCHMARKS.md)** - Detailed performance analysis and targets
- **[API Documentation](../docs/API.md)** - REST API integration details
- **[Contributing Guide](../CONTRIBUTING.md)** - How to contribute

---

## 🚀 Quick Start

### Prerequisites

**System Requirements:**
- **Obsidian:** v0.15.0 or higher
- **Python:** 3.9+ (for MemoGraph backend)
- **RAM:** 4GB minimum, 8GB recommended
- **Storage:** SSD recommended for best performance

**Install MemoGraph Backend:**
```bash
# Install via pip
pip install memograph

# Verify installation
memograph --version
```

### Installation (3 Steps)

#### Step 1: Install Plugin

**Option A: Community Plugins (Coming Soon)**
1. Open Obsidian Settings
2. Go to Community Plugins → Browse
3. Search for "MemoGraph Sync"
4. Click Install and Enable

**Option B: Manual Installation (Current)**
1. Download latest release from [GitHub Releases](https://github.com/Indhar01/MemoGraph/releases)
2. Extract to `<vault>/.obsidian/plugins/memograph-sync/`
3. Enable in Settings → Community Plugins

**Option C: Build from Source**
```bash
git clone https://github.com/Indhar01/MemoGraph.git
cd MemoGraph/obsidian-plugin
npm install
npm run build
```

#### Step 2: Configure Settings

1. Open Obsidian Settings → MemoGraph Sync
2. Set vault paths:
   - **Obsidian Vault:** Auto-detected (verify)
   - **MemoGraph Vault:** `~/.memograph/vaults/obsidian`
3. Enable Auto-sync (recommended)
4. Choose conflict strategy: "Newest Wins" (default)

#### Step 3: First Sync

1. Open Command Palette (`Ctrl/Cmd+P`)
2. Run: `MemoGraph: Sync All Notes`
3. Wait for completion (~30 seconds for 100 notes)
4. Check Status Dashboard for confirmation

**✅ Done!** Your notes are now synced.

---

## ⚙️ Configuration

### Sync Settings

| Setting | Default | Range | Description |
|---------|---------|-------|-------------|
| Auto-sync | Enabled | On/Off | Automatic synchronization |
| Debounce Delay | 300ms | 100-1000ms | Wait time before sync |
| Batch Size | 50 | 10-100 | Files per batch |
| Sync Direction | Bidirectional | 3 options | Push, Pull, or Both |

### Conflict Resolution

| Strategy | When to Use | Behavior |
|----------|-------------|----------|
| Newest Wins | General use (default) | Keep most recent version |
| Obsidian Wins | Obsidian is source of truth | Always prefer Obsidian |
| MemoGraph Wins | MemoGraph is authoritative | Always prefer MemoGraph |
| Manual | Critical notes | Show modal for user decision |

### Performance Options

```yaml
# In ~/.memograph/config/obsidian.yaml
use_sqlite: true          # Enable SQLite (2-3x faster)
enable_cache: true        # Enable LRU cache (21x speedup)
cache_size: 256          # Cache entries
batch_size: 50           # Files per batch
```

---

## 💡 Usage Examples

### Daily Workflow

```markdown
1. Create daily note in Obsidian
2. Auto-sync happens in background (300ms after typing stops)
3. Access note via MemoGraph API
4. Edit on another device via MemoGraph
5. Pull changes back to Obsidian
```

### Batch Sync Large Vault

```
1. Command Palette → "MemoGraph: Batch Sync All Files"
2. Watch progress: [████████████░░░░░░░░░░░░ 45%]
3. Cancel anytime with "Cancel" button
4. Resume after error with "Resume Sync"
```

### Conflict Resolution

```
1. Edit note in both Obsidian and MemoGraph
2. Conflict modal appears automatically
3. View side-by-side diff
4. Choose: Keep Obsidian / Keep MemoGraph / Keep Both / Manual
5. Conflict logged in history for review
```

### Performance Monitoring

```
1. Open Status Dashboard: "MemoGraph: Open Sync Status Dashboard"
2. View statistics:
   - Total syncs: 127
   - Success rate: 98.4%
   - Average duration: 8.5s
   - Files/sec: 11.8
3. Review recent history and errors
```

---

## 🎯 Performance Targets

| Vault Size | Initial Sync | Incremental | Auto-Sync | Memory |
|-----------|-------------|-------------|-----------|---------|
| 10 files | < 5s | < 1s | < 1s | < 50 MB |
| 100 files | < 30s | < 5s | < 2s | < 200 MB |
| 500 files | < 120s | < 10s | < 3s | < 500 MB |
| 1000 files | < 300s | < 20s | < 5s | < 1 GB |

**Throughput:** 3-12 files/second (varies by file complexity)
**Cache Hit Rate:** 95%+ in typical usage
**Speedup vs v0.1.0:** 2-5x faster overall

See [Performance Benchmarks](../docs/PERFORMANCE_BENCHMARKS.md) for detailed analysis.

---

## 🐛 Troubleshooting

### Quick Fixes

```bash
# Fix 1: Reset sync state
memograph reset-sync --vault ~/.memograph/vaults/obsidian

# Fix 2: Clear cache
rm -rf ~/.memograph/cache/*

# Fix 3: Check logs
tail -f ~/.memograph/logs/sync.log
```

### Common Issues

**Plugin not showing:**
- Verify files in `.obsidian/plugins/memograph-sync/`
- Restart Obsidian
- Check Developer Console (`Ctrl+Shift+I`)

**Sync failing:**
- Verify both vaults accessible
- Check permissions: `chmod -R u+rw <vault-path>`
- Test manual sync: Command → "MemoGraph: Sync All Notes"

**Slow performance:**
- Enable SQLite backend
- Enable LRU caching
- Reduce batch size to 25
- Exclude large files (PDFs, images)

See [Troubleshooting Guide](../docs/TROUBLESHOOTING.md) for detailed solutions.

---

## 🔧 Development

### Setup Development Environment

```bash
# Clone repository
git clone https://github.com/Indhar01/MemoGraph.git
cd MemoGraph/obsidian-plugin

# Install dependencies
npm install

# Build plugin
npm run build

# Development mode (auto-rebuild)
npm run dev
```

### Project Structure

```
obsidian-plugin/
├── src/
│   ├── main.ts              # Plugin entry point
│   ├── settings.ts          # Settings UI and management
│   ├── sync.ts              # Sync logic and API
│   ├── conflictModal.ts     # Conflict resolution UI
│   ├── diffView.ts          # Side-by-side diff component
│   ├── statusView.ts        # Status dashboard
│   └── syncStats.ts         # Statistics tracking
├── manifest.json            # Plugin metadata
├── package.json             # Dependencies
├── tsconfig.json            # TypeScript config
└── esbuild.config.mjs       # Build configuration
```

### Testing

```bash
# Build for testing
npm run build

# Create symlink to test vault
ln -s /path/to/obsidian-plugin \
      /path/to/test-vault/.obsidian/plugins/memograph-sync

# Reload Obsidian (Ctrl/Cmd+R)
```

### Code Style

- **TypeScript:** Strict mode enabled
- **Formatting:** Prettier (2 spaces, no semicolons)
- **Linting:** ESLint with Obsidian plugin rules
- **Testing:** Manual testing in Obsidian

---

## 📊 Architecture

### Component Overview

```
┌─────────────────┐      ┌──────────────────┐
│  Obsidian UI    │◄────►│  Plugin Core     │
│  - Commands     │      │  - Lifecycle     │
│  - Ribbon       │      │  - Events        │
│  - Modals       │      │  - State         │
└─────────────────┘      └──────────────────┘
                                  │
                                  ▼
         ┌────────────────────────────────────┐
         │        Sync Manager                │
         │  - Auto-sync with debouncing       │
         │  - Batch operations                │
         │  - Conflict detection              │
         │  - Error handling & retry          │
         └────────────────────────────────────┘
                          │
                          ▼
         ┌────────────────────────────────────┐
         │     MemoGraph Python Backend       │
         │  - File parsing                    │
         │  - SQLite storage                  │
         │  - Graph operations                │
         │  - Search & retrieval              │
         └────────────────────────────────────┘
```

### Data Flow

```
User Edit → Debounce (300ms) → Detect Changes → Batch Files
    → Sync to MemoGraph → Update State → Update UI

Conflict Detected → Show Modal → User Choice → Resolve
    → Log History → Continue Sync
```

---

## 🗺️ Roadmap

### ✅ Completed (v0.2.0)

- [x] Bidirectional sync
- [x] Auto-sync with debouncing
- [x] Conflict resolution strategies
- [x] Visual conflict resolution UI
- [x] Batch sync operations
- [x] SQLite backend
- [x] LRU caching
- [x] Optimized wikilink resolution
- [x] Status dashboard
- [x] Error handling & retry
- [x] Performance metrics
- [x] Conflict history

### 🚧 In Progress (v0.3.0)

- [ ] Real-time sync using WebSockets
- [ ] Mobile app support (iOS/Android)
- [ ] Attachment and image sync
- [ ] Graph visualization in Obsidian

### 📋 Planned (Future)

- [ ] Multi-vault support
- [ ] Selective folder sync with advanced filters
- [ ] Encrypted sync
- [ ] Cloud sync integration
- [ ] Collaboration features
- [ ] Version history and restore
- [ ] Custom sync rules

---

## 🤝 Contributing

We welcome contributions! Here's how to help:

1. **Report Bugs** - [Open an issue](https://github.com/Indhar01/MemoGraph/issues)
2. **Suggest Features** - [Start a discussion](https://github.com/Indhar01/MemoGraph/discussions)
3. **Submit PRs** - Fork, make changes, submit pull request
4. **Improve Docs** - Fix typos, add examples, clarify instructions
5. **Test** - Try beta versions and provide feedback

See [Contributing Guide](../CONTRIBUTING.md) for detailed guidelines.

---

## 📄 License

MIT License - see [LICENSE](../LICENSE) file

---

## 🔗 Links

- **[MemoGraph Repository](https://github.com/Indhar01/MemoGraph)** - Main project
- **[Documentation](../docs/)** - Complete documentation
- **[Releases](https://github.com/Indhar01/MemoGraph/releases)** - Download releases
- **[Issues](https://github.com/Indhar01/MemoGraph/issues)** - Report bugs
- **[Discussions](https://github.com/Indhar01/MemoGraph/discussions)** - Ask questions
- **[Changelog](CHANGELOG.md)** - Version history

---

## 📞 Support

### Getting Help

- **[Setup Guide](
