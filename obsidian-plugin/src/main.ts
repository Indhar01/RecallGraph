import { Plugin, Notice, TFile, WorkspaceLeaf } from 'obsidian';
import { MemoGraphSettings, DEFAULT_SETTINGS, MemoGraphSettingTab } from './settings';
import { SyncManager } from './sync';
import { SyncStatsManager } from './syncStats';
import { StatusView, STATUS_VIEW_TYPE } from './statusView';

export default class MemoGraphPlugin extends Plugin {
    settings!: MemoGraphSettings;
    syncManager!: SyncManager;
    statsManager!: SyncStatsManager;
    syncIntervalId: number | null = null;

    async onload() {
        console.log('Loading MemoGraph plugin');

        // Load settings
        await this.loadSettings();

        // Initialize statistics manager
        this.statsManager = new SyncStatsManager();

        // Initialize sync manager
        this.syncManager = new SyncManager(this.app, this.settings);

        // Register status view
        this.registerView(
            STATUS_VIEW_TYPE,
            (leaf) => new StatusView(leaf, this.statsManager, this.syncManager)
        );

        // Add ribbon icon
        this.addRibbonIcon('sync', 'Sync with MemoGraph', async () => {
            const startTime = this.statsManager.recordSyncStart('bidirectional');
            new Notice('Syncing with MemoGraph...');
            const stats = await this.syncManager.sync();
            this.statsManager.recordSyncEnd(
                startTime,
                'bidirectional',
                stats.pulled,
                stats.pushed,
                stats.conflicts,
                stats.errors
            );
            new Notice('Sync complete!');
            this.refreshStatusView();
        });

        // Add sync command
        this.addCommand({
            id: 'sync-memograph',
            name: 'Sync with MemoGraph',
            callback: async () => {
                const startTime = this.statsManager.recordSyncStart('bidirectional');
                new Notice('Syncing with MemoGraph...');
                const stats = await this.syncManager.sync();
                this.statsManager.recordSyncEnd(
                    startTime,
                    'bidirectional',
                    stats.pulled,
                    stats.pushed,
                    stats.conflicts,
                    stats.errors
                );
                new Notice(`Sync complete: ↓${stats.pulled} ↑${stats.pushed}`);
                this.refreshStatusView();
            }
        });

        // Add status view command
        this.addCommand({
            id: 'open-sync-status',
            name: 'Open Sync Status Dashboard',
            callback: () => {
                this.activateStatusView();
            }
        });

        // Add batch sync command
        this.addCommand({
            id: 'batch-sync',
            name: 'Batch Sync All Files',
            callback: async () => {
                const startTime = this.statsManager.recordSyncStart('bidirectional');
                const stats = await this.syncManager.batchSyncWithProgress();
                this.statsManager.recordSyncEnd(
                    startTime,
                    'bidirectional',
                    stats.pulled || 0,
                    stats.pushed || 0,
                    stats.conflicts || 0,
                    stats.errors || [],
                    stats.cancelled || false
                );
                this.refreshStatusView();
            }
        });

        // Add conflict history command
        this.addCommand({
            id: 'view-conflict-history',
            name: 'View Conflict History',
            callback: () => {
                const history = this.syncManager.getConflictHistory();
                if (history.length === 0) {
                    new Notice('No conflicts recorded');
                } else {
                    const summary = history.map((c, i) =>
                        `${i + 1}. ${c.filePath} - ${c.resolution} (${c.autoResolved ? 'auto' : 'manual'})`
                    ).join('\n');
                    new Notice(`Conflict History:\n${summary}`, 10000);
                }
            }
        });

        // Add clear conflict history command
        this.addCommand({
            id: 'clear-conflict-history',
            name: 'Clear Conflict History',
            callback: () => {
                this.syncManager.clearConflictHistory();
                new Notice('Conflict history cleared');
            }
        });

        // Add settings tab
        this.addSettingTab(new MemoGraphSettingTab(this.app, this));

        // Auto-sync on file changes (if enabled)
        if (this.settings.autoSync) {
            this.enableAutoSync();
        }
    }

    async onunload() {
        console.log('Unloading MemoGraph plugin');
        this.disableAutoSync();
    }

    async loadSettings() {
        this.settings = Object.assign({}, DEFAULT_SETTINGS, await this.loadData());
    }

    async saveSettings() {
        await this.saveData(this.settings);
        
        // Restart auto-sync if settings changed
        if (this.settings.autoSync) {
            this.enableAutoSync();
        } else {
            this.disableAutoSync();
        }
    }

    enableAutoSync() {
        // Clear existing interval
        this.disableAutoSync();

        // Set up periodic sync
        this.syncIntervalId = window.setInterval(
            async () => {
                console.log('Auto-syncing with MemoGraph...');
                await this.syncManager.sync();
            },
            this.settings.syncInterval * 1000
        );

        // Also sync on file modifications
        this.registerEvent(
            this.app.vault.on('modify', async (file) => {
                if (file instanceof TFile && file.extension === 'md') {
                    await this.syncManager.syncFile(file);
                }
            })
        );
    }

    disableAutoSync() {
        if (this.syncIntervalId !== null) {
            window.clearInterval(this.syncIntervalId);
            this.syncIntervalId = null;
        }
    }

    async activateStatusView(): Promise<void> {
        const { workspace } = this.app;

        let leaf: WorkspaceLeaf | null = null;
        const leaves = workspace.getLeavesOfType(STATUS_VIEW_TYPE);

        if (leaves.length > 0) {
            // View already exists, reveal it
            leaf = leaves[0];
        } else {
            // Create new view in right sidebar
            leaf = workspace.getRightLeaf(false);
            if (leaf) {
                await leaf.setViewState({ type: STATUS_VIEW_TYPE, active: true });
            }
        }

        // Reveal the leaf
        if (leaf) {
            workspace.revealLeaf(leaf);
        }
    }

    refreshStatusView(): void {
        const leaves = this.app.workspace.getLeavesOfType(STATUS_VIEW_TYPE);
        leaves.forEach(leaf => {
            const view = leaf.view;
            if (view instanceof StatusView) {
                view.refresh();
            }
        });
    }
}