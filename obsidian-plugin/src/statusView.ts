/**
 * Status view for displaying sync progress and statistics
 */

import { ItemView, WorkspaceLeaf, Notice } from 'obsidian';
import { SyncStatsManager, SyncStatistics, SyncHistoryEntry } from './syncStats';
import { SyncManager } from './sync';

export const STATUS_VIEW_TYPE = 'memograph-status-view';

export class StatusView extends ItemView {
    private statsManager: SyncStatsManager;
    private syncManager: SyncManager;
    private refreshInterval: number | null = null;
    private container: HTMLElement | null = null;

    constructor(leaf: WorkspaceLeaf, statsManager: SyncStatsManager, syncManager: SyncManager) {
        super(leaf);
        this.statsManager = statsManager;
        this.syncManager = syncManager;
    }

    getViewType(): string {
        return STATUS_VIEW_TYPE;
    }

    getDisplayText(): string {
        return 'MemoGraph Sync Status';
    }

    getIcon(): string {
        return 'sync';
    }

    async onOpen(): Promise<void> {
        this.container = this.containerEl.children[1] as HTMLElement;
        this.container.empty();
        this.container.addClass('memograph-status-view');

        this.render();

        // Auto-refresh every 5 seconds
        this.refreshInterval = window.setInterval(() => {
            this.render();
        }, 5000);
    }

    async onClose(): Promise<void> {
        if (this.refreshInterval !== null) {
            window.clearInterval(this.refreshInterval);
            this.refreshInterval = null;
        }
    }

    refresh(): void {
        this.render();
    }

    private render(): void {
        if (!this.container) return;

        this.container.empty();

        // Add custom styles
        this.addStyles();

        // Current Sync Status
        this.renderCurrentStatus();

        // Statistics Summary
        this.renderStatistics();

        // Sync History
        this.renderHistory();

        // Error Log
        this.renderErrors();

        // Action Buttons
        this.renderActions();
    }

    private addStyles(): void {
        const styleId = 'memograph-status-styles';
        if (document.getElementById(styleId)) return;

        const style = document.createElement('style');
        style.id = styleId;
        style.textContent = `
            .memograph-status-view {
                padding: 20px;
                overflow-y: auto;
            }
            .status-section {
                margin-bottom: 20px;
                padding: 15px;
                border: 1px solid var(--background-modifier-border);
                border-radius: 5px;
            }
            .status-section h3 {
                margin-top: 0;
                margin-bottom: 10px;
                color: var(--text-accent);
            }
            .status-row {
                display: flex;
                justify-content: space-between;
                padding: 5px 0;
                border-bottom: 1px solid var(--background-modifier-border);
            }
            .status-row:last-child {
                border-bottom: none;
            }
            .status-label {
                font-weight: 500;
            }
            .status-value {
                color: var(--text-muted);
            }
            .status-badge {
                display: inline-block;
                padding: 2px 8px;
                border-radius: 3px;
                font-size: 0.9em;
                font-weight: 500;
            }
            .status-badge.success {
                background-color: var(--background-modifier-success);
                color: var(--text-on-accent);
            }
            .status-badge.error {
                background-color: var(--background-modifier-error);
                color: var(--text-on-accent);
            }
            .status-badge.syncing {
                background-color: var(--interactive-accent);
                color: var(--text-on-accent);
            }
            .status-badge.idle {
                background-color: var(--background-modifier-border);
                color: var(--text-normal);
            }
            .progress-bar {
                width: 100%;
                height: 20px;
                background-color: var(--background-modifier-border);
                border-radius: 10px;
                overflow: hidden;
                margin: 10px 0;
            }
            .progress-fill {
                height: 100%;
                background-color: var(--interactive-accent);
                transition: width 0.3s ease;
                display: flex;
                align-items: center;
                justify-content: center;
                color: var(--text-on-accent);
                font-size: 0.8em;
                font-weight: 500;
            }
            .history-entry {
                padding: 8px;
                margin: 5px 0;
                background-color: var(--background-secondary);
                border-radius: 3px;
            }
            .history-timestamp {
                font-size: 0.85em;
                color: var(--text-muted);
            }
            .error-entry {
                padding: 8px;
                margin: 5px 0;
                background-color: var(--background-modifier-error);
                border-radius: 3px;
                font-size: 0.9em;
            }
            .action-buttons {
                display: flex;
                gap: 10px;
                flex-wrap: wrap;
            }
            .action-button {
                padding: 8px 15px;
                background-color: var(--interactive-accent);
                color: var(--text-on-accent);
                border: none;
                border-radius: 3px;
                cursor: pointer;
                font-size: 0.9em;
            }
            .action-button:hover {
                opacity: 0.8;
            }
            .action-button.secondary {
                background-color: var(--background-modifier-border);
                color: var(--text-normal);
            }
        `;
        document.head.appendChild(style);
    }

    private renderCurrentStatus(): void {
        const section = this.container!.createDiv({ cls: 'status-section' });
        section.createEl('h3', { text: 'Current Status' });

        const queueStatus = this.syncManager.getSyncQueueStatus();
        const batchStatus = this.syncManager.getBatchSyncStatus();
        const isSyncing = queueStatus.syncing || batchStatus.syncing;

        // Status badge
        const statusRow = section.createDiv({ cls: 'status-row' });
        statusRow.createSpan({ cls: 'status-label', text: 'Status:' });

        let badgeText = 'Idle';
        let badgeClass = 'idle';

        if (isSyncing) {
            badgeText = 'Syncing';
            badgeClass = 'syncing';
        } else if (queueStatus.queued > 0) {
            badgeText = `${queueStatus.queued} Queued`;
            badgeClass = 'idle';
        }

        const badge = statusRow.createSpan({
            cls: `status-badge ${badgeClass}`,
            text: badgeText
        });

        // Queue info
        if (queueStatus.queued > 0) {
            const queueRow = section.createDiv({ cls: 'status-row' });
            queueRow.createSpan({ cls: 'status-label', text: 'Queued Files:' });
            queueRow.createSpan({
                cls: 'status-value',
                text: queueStatus.queued.toString()
            });

            // Show queued file names (first 5)
            const fileList = queueStatus.queuedFiles.slice(0, 5);
            if (fileList.length > 0) {
                const filesDiv = section.createDiv({ cls: 'status-row' });
                filesDiv.createSpan({ cls: 'status-label', text: 'Files:' });
                const fileNames = filesDiv.createDiv({ cls: 'status-value' });
                fileList.forEach(file => {
                    fileNames.createEl('div', {
                        text: `• ${file.split('/').pop()}`,
                        cls: 'file-name'
                    });
                });
                if (queueStatus.queued > 5) {
                    fileNames.createEl('div', {
                        text: `... and ${queueStatus.queued - 5} more`,
                        cls: 'file-name'
                    });
                }
            }
        }

        // Last sync time
        const stats = this.statsManager.getStatistics();
        if (stats.lastSyncTime) {
            const lastSyncRow = section.createDiv({ cls: 'status-row' });
            lastSyncRow.createSpan({ cls: 'status-label', text: 'Last Sync:' });
            lastSyncRow.createSpan({
                cls: 'status-value',
                text: new Date(stats.lastSyncTime).toLocaleString()
            });
        }
    }

    private formatTimestamp(timestamp: number): string {
        const now = Date.now();
        const diff = now - timestamp;

        if (diff < 60000) return 'Just now';
        if (diff < 3600000) return `${Math.floor(diff / 60000)} minutes ago`;
        if (diff < 86400000) return `${Math.floor(diff / 3600000)} hours ago`;

        return new Date(timestamp).toLocaleString();
    }

    private renderStatistics(): void {
        const section = this.container!.createDiv({ cls: 'status-section' });
        section.createEl('h3', { text: 'Statistics' });

        const stats = this.statsManager.getStatistics();
        const averages = this.statsManager.getAverageFilesPerSync();
        const successRate = this.statsManager.getSuccessRate();

        const rows = [
            { label: 'Total Syncs', value: stats.totalSyncs.toString() },
            { label: 'Successful', value: stats.successfulSyncs.toString() },
            { label: 'Failed', value: stats.failedSyncs.toString() },
            { label: 'Success Rate', value: `${successRate.toFixed(1)}%` },
            { label: 'Files Pulled', value: stats.filesPulled.toString() },
            { label: 'Files Pushed', value: stats.filesPushed.toString() },
            { label: 'Conflicts Resolved', value: stats.conflictsResolved.toString() },
            { label: 'Total Errors', value: stats.totalErrors.toString() },
            {
                label: 'Avg. Duration',
                value: this.statsManager.formatDuration(stats.averageSyncDuration)
            },
            {
                label: 'Avg. Files/Sync',
                value: `↓${averages.pulled.toFixed(1)} ↑${averages.pushed.toFixed(1)}`
            }
        ];

        rows.forEach(row => {
            const rowEl = section.createDiv({ cls: 'status-row' });
            rowEl.createSpan({ cls: 'status-label', text: row.label + ':' });
            rowEl.createSpan({ cls: 'status-value', text: row.value });
        });

        // Success rate progress bar
        if (stats.totalSyncs > 0) {
            section.createEl('div', { text: 'Success Rate', cls: 'status-label' });
            const progressBar = section.createDiv({ cls: 'progress-bar' });
            const progressFill = progressBar.createDiv({ cls: 'progress-fill' });
            progressFill.style.width = `${successRate}%`;
            progressFill.setText(`${successRate.toFixed(1)}%`);
        }
    }

    private renderHistory(): void {
        const section = this.container!.createDiv({ cls: 'status-section' });
        section.createEl('h3', { text: 'Recent Sync History' });

        const history = this.statsManager.getHistory(10);

        if (history.length === 0) {
            section.createDiv({
                cls: 'status-value',
                text: 'No sync history available'
            });
            return;
        }

        history.forEach(entry => {
            const entryDiv = section.createDiv({ cls: 'history-entry' });

            const timestampDiv = entryDiv.createDiv({ cls: 'history-timestamp' });
            timestampDiv.setText(new Date(entry.timestamp).toLocaleString());

            const statusBadge = entryDiv.createSpan({
                cls: `status-badge ${entry.status === 'success' ? 'success' : 'error'}`,
                text: entry.status.toUpperCase()
            });

            const detailsDiv = entryDiv.createDiv();
            detailsDiv.setText(
                `${entry.direction.toUpperCase()} - ` +
                `↓${entry.pulled} ↑${entry.pushed} ` +
                `⚠${entry.conflicts} conflicts ` +
                `(${this.statsManager.formatDuration(entry.duration)})`
            );

            if (entry.errors.length > 0) {
                const errorsDiv = entryDiv.createDiv({ cls: 'error-entry' });
                errorsDiv.setText(`Errors: ${entry.errors.length}`);
            }
        });
    }

    private renderErrors(): void {
        const recentErrors = this.statsManager.getRecentErrors(5);

        if (recentErrors.length === 0) return;

        const section = this.container!.createDiv({ cls: 'status-section' });
        section.createEl('h3', { text: 'Recent Errors' });

        recentErrors.forEach(error => {
            const errorDiv = section.createDiv({ cls: 'error-entry' });
            errorDiv.setText(error);
        });
    }

    private renderActions(): void {
        const section = this.container!.createDiv({ cls: 'status-section' });
        section.createEl('h3', { text: 'Actions' });

        const buttonsDiv = section.createDiv({ cls: 'action-buttons' });

        // Refresh button
        const refreshBtn = buttonsDiv.createEl('button', {
            cls: 'action-button',
            text: 'Refresh'
        });
        refreshBtn.addEventListener('click', () => {
            this.refresh();
            new Notice('Status refreshed');
        });

        // Clear history button
        const clearHistoryBtn = buttonsDiv.createEl('button', {
            cls: 'action-button secondary',
            text: 'Clear History'
        });
        clearHistoryBtn.addEventListener('click', () => {
            this.statsManager.clearHistory();
            this.refresh();
            new Notice('Sync history cleared');
        });

        // Reset statistics button
        const resetStatsBtn = buttonsDiv.createEl('button', {
            cls: 'action-button secondary',
            text: 'Reset Statistics'
        });
        resetStatsBtn.addEventListener('click', () => {
            this.statsManager.resetStatistics();
            this.refresh();
            new Notice('Statistics reset');
        });

        // Cancel batch sync button (only show if syncing)
        const batchStatus = this.syncManager.getBatchSyncStatus();
        if (batchStatus.syncing) {
            const cancelBtn = buttonsDiv.createEl('button', {
                cls: 'action-button secondary',
                text: 'Cancel Batch Sync'
            });
            cancelBtn.addEventListener('click', () => {
                this.syncManager.cancelBatchSync();
                new Notice('Cancelling batch sync...');
                setTimeout(() => this.refresh(), 1000);
            });
        }
    }
}
