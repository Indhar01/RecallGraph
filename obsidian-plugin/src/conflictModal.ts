import { App, Modal, Notice, TFile } from 'obsidian';

export interface ConflictData {
    filePath: string;
    localVersion: string;
    remoteVersion: string;
    localModified: number;
    remoteModified: number;
}

export type ConflictResolution = 'keep-local' | 'keep-remote' | 'keep-both' | 'manual';

export class ConflictModal extends Modal {
    conflictData: ConflictData;
    onResolve: (resolution: ConflictResolution, mergedContent?: string) => void;
    diffViewEl: HTMLElement | null = null;
    
    constructor(
        app: App,
        conflictData: ConflictData,
        onResolve: (resolution: ConflictResolution, mergedContent?: string) => void
    ) {
        super(app);
        this.conflictData = conflictData;
        this.onResolve = onResolve;
    }

    onOpen() {
        const { contentEl } = this;
        
        contentEl.empty();
        contentEl.addClass('memograph-conflict-modal');
        
        // Header
        contentEl.createEl('h2', { text: 'Sync Conflict Detected' });
        contentEl.createEl('p', {
            text: `The file "${this.conflictData.filePath}" has conflicting changes.`,
            cls: 'conflict-description'
        });

        // Timestamps
        const timeInfo = contentEl.createDiv({ cls: 'conflict-time-info' });
        timeInfo.createEl('div', {
            text: `Local version: ${new Date(this.conflictData.localModified).toLocaleString()}`
        });
        timeInfo.createEl('div', {
            text: `Remote version: ${new Date(this.conflictData.remoteModified).toLocaleString()}`
        });

        // Create diff view container
        this.diffViewEl = contentEl.createDiv({ cls: 'conflict-diff-container' });
        this.renderDiffView();

        // Action buttons
        const buttonContainer = contentEl.createDiv({ cls: 'conflict-button-container' });
        
        // Keep Local button
        const keepLocalBtn = buttonContainer.createEl('button', {
            text: 'Keep Local Version',
            cls: 'mod-cta'
        });
        keepLocalBtn.addEventListener('click', () => {
            this.onResolve('keep-local');
            this.close();
        });

        // Keep Remote button
        const keepRemoteBtn = buttonContainer.createEl('button', {
            text: 'Keep Remote Version',
            cls: 'mod-cta'
        });
        keepRemoteBtn.addEventListener('click', () => {
            this.onResolve('keep-remote');
            this.close();
        });

        // Keep Both button
        const keepBothBtn = buttonContainer.createEl('button', {
            text: 'Keep Both (Merge)',
            cls: 'mod-warning'
        });
        keepBothBtn.addEventListener('click', () => {
            const mergedContent = this.createMergedVersion();
            this.onResolve('keep-both', mergedContent);
            this.close();
        });

        // Manual Edit button
        const manualBtn = buttonContainer.createEl('button', {
            text: 'Edit Manually',
        });
        manualBtn.addEventListener('click', () => {
            this.onResolve('manual');
            this.close();
        });

        // Cancel button
        const cancelBtn = buttonContainer.createEl('button', {
            text: 'Cancel',
        });
        cancelBtn.addEventListener('click', () => {
            this.close();
        });

        // Add CSS
        this.addStyles();
    }

    renderDiffView() {
        if (!this.diffViewEl) return;

        this.diffViewEl.empty();

        // Create side-by-side comparison
        const comparisonContainer = this.diffViewEl.createDiv({ cls: 'conflict-comparison' });

        // Local version panel
        const localPanel = comparisonContainer.createDiv({ cls: 'conflict-panel conflict-local' });
        localPanel.createEl('h3', { text: 'Local Version' });
        const localContent = localPanel.createEl('pre', { cls: 'conflict-content' });
        localContent.createEl('code', { text: this.conflictData.localVersion });

        // Remote version panel
        const remotePanel = comparisonContainer.createDiv({ cls: 'conflict-panel conflict-remote' });
        remotePanel.createEl('h3', { text: 'Remote Version (MemoGraph)' });
        const remoteContent = remotePanel.createEl('pre', { cls: 'conflict-content' });
        remoteContent.createEl('code', { text: this.conflictData.remoteVersion });

        // Show diff highlights
        this.highlightDifferences(localContent, remoteContent);
    }

    highlightDifferences(localEl: HTMLElement, remoteEl: HTMLElement) {
        // Simple line-by-line diff highlighting
        const localLines = this.conflictData.localVersion.split('\n');
        const remoteLines = this.conflictData.remoteVersion.split('\n');

        const maxLines = Math.max(localLines.length, remoteLines.length);
        let diffCount = 0;

        for (let i = 0; i < maxLines; i++) {
            const localLine = localLines[i] || '';
            const remoteLine = remoteLines[i] || '';

            if (localLine !== remoteLine) {
                diffCount++;
            }
        }

        // Add diff summary
        const summary = this.diffViewEl?.createDiv({ cls: 'conflict-diff-summary' });
        if (summary) {
            summary.createEl('p', {
                text: `Found ${diffCount} differing lines between versions.`
            });
        }
    }

    createMergedVersion(): string {
        // Create a merged version with conflict markers
        const merged = `<<<<<<< Local Version (${new Date(this.conflictData.localModified).toLocaleString()})
${this.conflictData.localVersion}
=======
${this.conflictData.remoteVersion}
>>>>>>> Remote Version (MemoGraph) (${new Date(this.conflictData.remoteModified).toLocaleString()})
`;
        return merged;
    }

    addStyles() {
        // Inject CSS styles for the modal
        const styleEl = document.createElement('style');
        styleEl.textContent = `
            .memograph-conflict-modal {
                padding: 20px;
            }

            .conflict-description {
                margin: 10px 0 20px 0;
                color: var(--text-muted);
            }

            .conflict-time-info {
                margin-bottom: 20px;
                padding: 10px;
                background: var(--background-secondary);
                border-radius: 5px;
            }

            .conflict-time-info div {
                margin: 5px 0;
                font-size: 0.9em;
            }

            .conflict-diff-container {
                margin: 20px 0;
                max-height: 400px;
                overflow-y: auto;
                border: 1px solid var(--background-modifier-border);
                border-radius: 5px;
            }

            .conflict-comparison {
                display: flex;
                gap: 10px;
            }

            .conflict-panel {
                flex: 1;
                padding: 10px;
            }

            .conflict-panel h3 {
                margin: 0 0 10px 0;
                font-size: 1em;
                font-weight: 600;
            }

            .conflict-local {
                background: var(--background-secondary);
                border-right: 2px solid var(--interactive-accent);
            }

            .conflict-remote {
                background: var(--background-secondary-alt);
            }

            .conflict-content {
                margin: 0;
                padding: 10px;
                background: var(--background-primary);
                border-radius: 3px;
                font-family: var(--font-monospace);
                font-size: 0.85em;
                white-space: pre-wrap;
                word-wrap: break-word;
                max-height: 300px;
                overflow-y: auto;
            }

            .conflict-diff-summary {
                padding: 10px;
                background: var(--background-secondary);
                border-top: 1px solid var(--background-modifier-border);
                text-align: center;
            }

            .conflict-button-container {
                display: flex;
                gap: 10px;
                justify-content: center;
                margin-top: 20px;
                flex-wrap: wrap;
            }

            .conflict-button-container button {
                padding: 8px 16px;
                cursor: pointer;
            }
        `;
        document.head.appendChild(styleEl);
    }

    onClose() {
        const { contentEl } = this;
        contentEl.empty();
    }
}