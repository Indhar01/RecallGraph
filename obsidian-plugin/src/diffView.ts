/**
 * Diff view component for showing differences between two versions of text
 */

export interface DiffLine {
    type: 'added' | 'removed' | 'unchanged' | 'modified';
    content: string;
    lineNumber: number;
    pairLineNumber?: number;
}

export interface DiffResult {
    localLines: DiffLine[];
    remoteLines: DiffLine[];
    stats: {
        added: number;
        removed: number;
        modified: number;
        unchanged: number;
    };
}

export class DiffView {
    /**
     * Compute diff between two text versions
     */
    static computeDiff(localText: string, remoteText: string): DiffResult {
        const localLines = localText.split('\n');
        const remoteLines = remoteText.split('\n');

        const diffResult: DiffResult = {
            localLines: [],
            remoteLines: [],
            stats: {
                added: 0,
                removed: 0,
                modified: 0,
                unchanged: 0
            }
        };

        // Use a simple line-by-line comparison
        // This could be enhanced with a more sophisticated diff algorithm like Myers
        const maxLines = Math.max(localLines.length, remoteLines.length);

        for (let i = 0; i < maxLines; i++) {
            const localLine = i < localLines.length ? localLines[i] : null;
            const remoteLine = i < remoteLines.length ? remoteLines[i] : null;

            if (localLine === null) {
                // Line only exists in remote (added)
                diffResult.remoteLines.push({
                    type: 'added',
                    content: remoteLine || '',
                    lineNumber: i + 1
                });
                diffResult.stats.added++;
            } else if (remoteLine === null) {
                // Line only exists in local (removed in remote)
                diffResult.localLines.push({
                    type: 'removed',
                    content: localLine,
                    lineNumber: i + 1
                });
                diffResult.stats.removed++;
            } else if (localLine === remoteLine) {
                // Lines are identical
                diffResult.localLines.push({
                    type: 'unchanged',
                    content: localLine,
                    lineNumber: i + 1,
                    pairLineNumber: i + 1
                });
                diffResult.remoteLines.push({
                    type: 'unchanged',
                    content: remoteLine,
                    lineNumber: i + 1,
                    pairLineNumber: i + 1
                });
                diffResult.stats.unchanged++;
            } else {
                // Lines are different (modified)
                diffResult.localLines.push({
                    type: 'modified',
                    content: localLine,
                    lineNumber: i + 1,
                    pairLineNumber: i + 1
                });
                diffResult.remoteLines.push({
                    type: 'modified',
                    content: remoteLine,
                    lineNumber: i + 1,
                    pairLineNumber: i + 1
                });
                diffResult.stats.modified++;
            }
        }

        return diffResult;
    }

    /**
     * Render unified diff view
     */
    static renderUnifiedDiff(container: HTMLElement, localText: string, remoteText: string): void {
        const diff = this.computeDiff(localText, remoteText);

        container.empty();
        container.addClass('memograph-diff-unified');

        // Stats header
        const statsEl = container.createDiv({ cls: 'diff-stats' });
        statsEl.createEl('span', {
            text: `${diff.stats.added} additions`,
            cls: 'diff-stat-added'
        });
        statsEl.createEl('span', { text: ' · ' });
        statsEl.createEl('span', {
            text: `${diff.stats.removed} deletions`,
            cls: 'diff-stat-removed'
        });
        statsEl.createEl('span', { text: ' · ' });
        statsEl.createEl('span', {
            text: `${diff.stats.modified} modifications`,
            cls: 'diff-stat-modified'
        });

        // Unified diff content
        const diffContent = container.createDiv({ cls: 'diff-content-unified' });

        // Merge local and remote lines for unified view
        const allLines = this.mergeForUnifiedView(diff);

        allLines.forEach(line => {
            const lineEl = diffContent.createDiv({ cls: `diff-line diff-line-${line.type}` });

            const lineNumber = lineEl.createEl('span', {
                cls: 'diff-line-number',
                text: line.lineNumber > 0 ? String(line.lineNumber) : ' '
            });

            const marker = lineEl.createEl('span', { cls: 'diff-line-marker' });
            if (line.type === 'added') {
                marker.textContent = '+ ';
            } else if (line.type === 'removed') {
                marker.textContent = '- ';
            } else if (line.type === 'modified') {
                marker.textContent = '~ ';
            } else {
                marker.textContent = '  ';
            }

            const content = lineEl.createEl('span', {
                cls: 'diff-line-content',
                text: line.content
            });
        });
    }

    /**
     * Render side-by-side diff view
     */
    static renderSideBySideDiff(container: HTMLElement, localText: string, remoteText: string): void {
        const diff = this.computeDiff(localText, remoteText);

        container.empty();
        container.addClass('memograph-diff-sidebyside');

        // Stats header
        const statsEl = container.createDiv({ cls: 'diff-stats' });
        statsEl.createEl('span', {
            text: `${diff.stats.added} additions`,
            cls: 'diff-stat-added'
        });
        statsEl.createEl('span', { text: ' · ' });
        statsEl.createEl('span', {
            text: `${diff.stats.removed} deletions`,
            cls: 'diff-stat-removed'
        });
        statsEl.createEl('span', { text: ' · ' });
        statsEl.createEl('span', {
            text: `${diff.stats.modified} modifications`,
            cls: 'diff-stat-modified'
        });

        // Side-by-side panels
        const panelsContainer = container.createDiv({ cls: 'diff-panels' });

        // Local panel
        const localPanel = panelsContainer.createDiv({ cls: 'diff-panel diff-panel-local' });
        localPanel.createEl('h4', { text: 'Local (Obsidian)' });
        const localContent = localPanel.createDiv({ cls: 'diff-content' });
        diff.localLines.forEach(line => {
            const lineEl = localContent.createDiv({ cls: `diff-line diff-line-${line.type}` });
            lineEl.createEl('span', { cls: 'diff-line-number', text: String(line.lineNumber) });
            lineEl.createEl('span', { cls: 'diff-line-content', text: line.content || ' ' });
        });

        // Remote panel
        const remotePanel = panelsContainer.createDiv({ cls: 'diff-panel diff-panel-remote' });
        remotePanel.createEl('h4', { text: 'Remote (MemoGraph)' });
        const remoteContent = remotePanel.createDiv({ cls: 'diff-content' });
        diff.remoteLines.forEach(line => {
            const lineEl = remoteContent.createDiv({ cls: `diff-line diff-line-${line.type}` });
            lineEl.createEl('span', { cls: 'diff-line-number', text: String(line.lineNumber) });
            lineEl.createEl('span', { cls: 'diff-line-content', text: line.content || ' ' });
        });
    }

    /**
     * Merge diff lines for unified view
     */
    private static mergeForUnifiedView(diff: DiffResult): Array<DiffLine & { side: 'local' | 'remote' }> {
        const merged: Array<DiffLine & { side: 'local' | 'remote' }> = [];

        let localIdx = 0;
        let remoteIdx = 0;

        while (localIdx < diff.localLines.length || remoteIdx < diff.remoteLines.length) {
            const localLine = localIdx < diff.localLines.length ? diff.localLines[localIdx] : null;
            const remoteLine = remoteIdx < diff.remoteLines.length ? diff.remoteLines[remoteIdx] : null;

            if (!localLine) {
                // Only remote line left
                merged.push({ ...remoteLine!, side: 'remote' });
                remoteIdx++;
            } else if (!remoteLine) {
                // Only local line left
                merged.push({ ...localLine, side: 'local' });
                localIdx++;
            } else if (localLine.type === 'unchanged' && remoteLine.type === 'unchanged') {
                // Both unchanged, show once
                merged.push({ ...localLine, side: 'local' });
                localIdx++;
                remoteIdx++;
            } else if (localLine.type === 'modified' && remoteLine.type === 'modified') {
                // Show both modified lines
                merged.push({ ...localLine, side: 'local' });
                merged.push({ ...remoteLine, side: 'remote' });
                localIdx++;
                remoteIdx++;
            } else {
                // One is removed, other is added
                if (localLine.type === 'removed') {
                    merged.push({ ...localLine, side: 'local' });
                    localIdx++;
                }
                if (remoteLine.type === 'added') {
                    merged.push({ ...remoteLine, side: 'remote' });
                    remoteIdx++;
                }
            }
        }

        return merged;
    }

    /**
     * Add styles for diff view
     */
    static addStyles(): void {
        if (document.getElementById('memograph-diff-styles')) {
            return; // Already added
        }

        const styleEl = document.createElement('style');
        styleEl.id = 'memograph-diff-styles';
        styleEl.textContent = `
            .memograph-diff-unified,
            .memograph-diff-sidebyside {
                font-family: var(--font-monospace);
                font-size: 0.85em;
            }

            .diff-stats {
                padding: 10px;
                background: var(--background-secondary);
                border-bottom: 1px solid var(--background-modifier-border);
                text-align: center;
            }

            .diff-stat-added {
                color: var(--text-success);
                font-weight: 600;
            }

            .diff-stat-removed {
                color: var(--text-error);
                font-weight: 600;
            }

            .diff-stat-modified {
                color: var(--text-warning);
                font-weight: 600;
            }

            .diff-content-unified {
                max-height: 400px;
                overflow-y: auto;
            }

            .diff-line {
                display: flex;
                padding: 2px 5px;
                line-height: 1.5;
            }

            .diff-line-number {
                display: inline-block;
                width: 40px;
                text-align: right;
                padding-right: 10px;
                color: var(--text-muted);
                user-select: none;
            }

            .diff-line-marker {
                width: 20px;
                font-weight: bold;
                user-select: none;
            }

            .diff-line-content {
                flex: 1;
                white-space: pre;
            }

            .diff-line-added {
                background: rgba(46, 160, 67, 0.15);
            }

            .diff-line-added .diff-line-marker {
                color: var(--text-success);
            }

            .diff-line-removed {
                background: rgba(248, 81, 73, 0.15);
            }

            .diff-line-removed .diff-line-marker {
                color: var(--text-error);
            }

            .diff-line-modified {
                background: rgba(219, 171, 9, 0.15);
            }

            .diff-line-modified .diff-line-marker {
                color: var(--text-warning);
            }

            .diff-line-unchanged {
                background: transparent;
            }

            .diff-panels {
                display: flex;
                gap: 2px;
                background: var(--background-modifier-border);
            }

            .diff-panel {
                flex: 1;
                background: var(--background-primary);
            }

            .diff-panel h4 {
                margin: 0;
                padding: 8px 10px;
                background: var(--background-secondary);
                border-bottom: 1px solid var(--background-modifier-border);
                font-size: 0.9em;
                font-weight: 600;
            }

            .diff-panel-local h4 {
                border-left: 3px solid var(--interactive-accent);
            }

            .diff-panel-remote h4 {
                border-left: 3px solid var(--text-accent);
            }

            .diff-panel .diff-content {
                max-height: 400px;
                overflow-y: auto;
            }
        `;
        document.head.appendChild(styleEl);
    }
}
