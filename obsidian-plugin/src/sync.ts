import { App, TFile, Notice } from 'obsidian';
import { MemoGraphSettings } from './settings';
import { ConflictModal, ConflictData, ConflictResolution } from './conflictModal';
import { DiffView } from './diffView';

export interface SyncStats {
    pulled: number;
    pushed: number;
    conflicts: number;
    errors: string[];
    cancelled?: boolean;
    processed?: number;
    duration?: number;
    timestamp?: number;
}

export interface BatchSyncOptions {
    batchSize?: number;
    direction?: 'pull' | 'push' | 'bidirectional';
    onProgress?: (current: number, total: number, file: string, status: string) => void;
}

export interface ConflictLog {
    filePath: string;
    timestamp: number;
    resolution: ConflictResolution;
    autoResolved: boolean;
}

export class SyncManager {
    app: App;
    settings: MemoGraphSettings;
    syncing: boolean;
    private debounceTimers: Map<string, ReturnType<typeof setTimeout>>;
    private syncQueue: Set<string>;
    private conflictHistory: ConflictLog[];
    private batchSyncing: boolean;
    private batchCancelled: boolean;
    private errorHistory: Array<{timestamp: number; message: string; type: string}>;

    constructor(app: App, settings: MemoGraphSettings) {
        this.app = app;
        this.settings = settings;
        this.syncing = false;
        this.debounceTimers = new Map();
        this.syncQueue = new Set();
        this.conflictHistory = [];
        this.batchSyncing = false;
        this.batchCancelled = false;
        this.errorHistory = [];

        // Initialize diff view styles
        DiffView.addStyles();
    }

    async batchSync(options: BatchSyncOptions = {}): Promise<SyncStats> {
        if (this.batchSyncing) {
            new Notice('Batch sync already in progress');
            return {
                pulled: 0,
                pushed: 0,
                conflicts: 0,
                errors: ['Batch sync already in progress'],
                cancelled: false,
                processed: 0,
                duration: 0,
                timestamp: Date.now()
            };
        }

        const startTime = Date.now();
        this.batchSyncing = true;
        this.batchCancelled = false;

        const {
            batchSize = 50,
            direction = 'bidirectional',
            onProgress
        } = options;

        const stats: SyncStats = {
            pulled: 0,
            pushed: 0,
            conflicts: 0,
            errors: [],
            cancelled: false,
            processed: 0,
            timestamp: startTime
        };

        try {
            const files = this.app.vault.getMarkdownFiles();
            const filteredFiles = this.filterFiles(files);
            const totalFiles = filteredFiles.length;

            if (totalFiles === 0) {
                new Notice('No files to sync');
                return stats;
            }

            new Notice(`Starting batch sync of ${totalFiles} files...`);

            // Process files in batches
            for (let i = 0; i < totalFiles; i += batchSize) {
                if (this.batchCancelled) {
                    stats.cancelled = true;
                    new Notice('Batch sync cancelled');
                    break;
                }

                const batch = filteredFiles.slice(i, Math.min(i + batchSize, totalFiles));

                // Process batch based on direction
                if (direction === 'pull' || direction === 'bidirectional') {
                    // For pull, we'd call the backend API
                    // This is simplified - in reality, you'd call your Python backend
                    if (onProgress) {
                        onProgress(i + batch.length, totalFiles, 'Pulling...', 'pull');
                    }
                }

                if (direction === 'push' || direction === 'bidirectional') {
                    for (let j = 0; j < batch.length; j++) {
                        if (this.batchCancelled) {
                            break;
                        }

                        const file = batch[j];
                        const currentIndex = i + j + 1;

                        if (onProgress) {
                            onProgress(currentIndex, totalFiles, file.path, 'pushing');
                        }

                        try {
                            await this.syncFile(file);
                            stats.pushed++;
                            stats.processed = (stats.processed || 0) + 1;
                        } catch (error) {
                            stats.errors.push(`Error syncing ${file.path}: ${error}`);
                        }
                    }
                }

                // Small delay between batches to prevent overwhelming the system
                await new Promise(resolve => setTimeout(resolve, 100));
            }

            const duration = Date.now() - startTime;
            stats.duration = duration;

            if (!stats.cancelled) {
                new Notice(
                    `Batch sync complete: ↓${stats.pulled} ↑${stats.pushed} ⚠${stats.conflicts} conflicts (${(duration / 1000).toFixed(1)}s)`
                );
            }

        } catch (error) {
            stats.errors.push(`Batch sync failed: ${error}`);
            new Notice(`Batch sync failed: ${error}`);
        } finally {
            this.batchSyncing = false;
            stats.duration = Date.now() - startTime;
        }

        return stats;
    }

    async batchSyncWithProgress(): Promise<SyncStats> {
        // Create a notice that we'll update with progress
        let progressNotice: Notice | null = null;

        const stats = await this.batchSync({
            batchSize: 50,
            direction: 'bidirectional',
            onProgress: (current, total, file, status) => {
                const percentage = Math.round((current / total) * 100);
                const message = `Syncing ${current}/${total} (${percentage}%) - ${status}: ${file}`;

                if (progressNotice) {
                    // Update existing notice
                    progressNotice.setMessage(message);
                } else {
                    progressNotice = new Notice(message, 0); // 0 = don't auto-dismiss
                }
            }
        });

        // Close progress notice
        if (progressNotice) {
            // @ts-ignore - hide() method exists but isn't in type definitions
            progressNotice.hide();
        }

        return stats;
    }

    cancelBatchSync(): void {
        if (this.batchSyncing) {
            this.batchCancelled = true;
            new Notice('Cancelling batch sync...');
        }
    }

    getBatchSyncStatus(): { syncing: boolean; cancelled: boolean } {
        return {
            syncing: this.batchSyncing,
            cancelled: this.batchCancelled
        };
    }

    async sync(): Promise<SyncStats> {
        if (this.syncing) {
            new Notice('Sync already in progress');
            return {
                pulled: 0,
                pushed: 0,
                conflicts: 0,
                errors: ['Sync already in progress'],
                duration: 0,
                timestamp: Date.now()
            };
        }

        const startTime = Date.now();
        this.syncing = true;
        const stats: SyncStats = {
            pulled: 0,
            pushed: 0,
            conflicts: 0,
            errors: [],
            timestamp: startTime
        };

        try {
            new Notice('Starting bidirectional sync with MemoGraph...');

            // Pull from MemoGraph first
            try {
                const pullStats = await this.pullFromMemoGraph();
                stats.pulled = pullStats.pulled;
                stats.conflicts += pullStats.conflicts;
                stats.errors.push(...pullStats.errors);
            } catch (error) {
                stats.errors.push(`Pull failed: ${error}`);
            }

            // Then push to MemoGraph
            const files = this.app.vault.getMarkdownFiles();
            const filteredFiles = this.filterFiles(files);

            for (const file of filteredFiles) {
                try {
                    await this.syncFile(file);
                    stats.pushed++;
                } catch (error) {
                    stats.errors.push(`Error syncing ${file.path}: ${error}`);
                }
            }

            const duration = Date.now() - startTime;
            stats.duration = duration;

            if (stats.errors.length === 0) {
                new Notice(`Sync complete: ↓${stats.pulled} ↑${stats.pushed} (${(duration / 1000).toFixed(1)}s)`);
            } else {
                new Notice(`Sync completed with ${stats.errors.length} errors`);
            }
        } catch (error) {
            stats.errors.push(`Sync failed: ${error}`);
            new Notice(`Sync failed: ${error}`);
        } finally {
            this.syncing = false;
            stats.duration = Date.now() - startTime;
        }

        return stats;
    }

    async syncFileDebounced(file: TFile): Promise<void> {
        const filePath = file.path;

        // Cancel existing debounce timer for this file
        if (this.debounceTimers.has(filePath)) {
            clearTimeout(this.debounceTimers.get(filePath)!);
        }

        // Set new debounce timer
        const timer = setTimeout(async () => {
            this.debounceTimers.delete(filePath);
            this.syncQueue.delete(filePath);

            try {
                await this.syncFile(file);
            } catch (error) {
                new Notice(`Failed to sync ${file.basename}: ${error}`);
            }
        }, this.settings.debounceDelay);

        this.debounceTimers.set(filePath, timer);
        this.syncQueue.add(filePath);
    }

    async syncFile(file: TFile): Promise<void> {
        const content = await this.app.vault.read(file);
        const metadata = this.app.metadataCache.getFileCache(file);

        // Extract frontmatter
        const frontmatter = metadata?.frontmatter || {};
        const tags = metadata?.tags?.map(t => t.tag) || [];

        // Prepare data for MemoGraph
        const data = {
            title: frontmatter.title || file.basename,
            content: content,
            tags: [...tags, ...(frontmatter.tags || [])],
            metadata: {
                ...frontmatter,
                source: 'obsidian',
                path: file.path,
                modified: file.stat.mtime
            }
        };

        // Send to MemoGraph API
        await this.pushToMemoGraph(data);
    }

    async pushToMemoGraph(data: any): Promise<void> {
        const operation = async () => {
            const url = `${this.settings.memoGraphUrl}/api/memories`;
            const headers: Record<string, string> = {
                'Content-Type': 'application/json'
            };

            if (this.settings.apiKey) {
                headers['Authorization'] = `Bearer ${this.settings.apiKey}`;
            }

            const response = await fetch(url, {
                method: 'POST',
                headers: headers,
                body: JSON.stringify(data)
            });

            if (!response.ok) {
                throw new Error(`MemoGraph API error: ${response.statusText}`);
            }
        };

        await this.retryWithBackoff(operation, 3, 1000);
    }

    async pullFromMemoGraph(): Promise<SyncStats> {
        const stats: SyncStats = {
            pulled: 0,
            pushed: 0,
            conflicts: 0,
            errors: []
        };

        try {
            // Fetch memories from MemoGraph API
            const memories = await this.fetchMemoriesFromMemoGraph();

            for (const memory of memories) {
                try {
                    // Convert memory to Obsidian format and save
                    await this.saveMemoryToVault(memory);
                    stats.pulled++;
                } catch (error) {
                    stats.errors.push(`Error pulling memory ${memory.id}: ${error}`);
                }
            }
        } catch (error) {
            stats.errors.push(`Failed to fetch memories: ${error}`);
            throw error;
        }

        return stats;
    }

    async fetchMemoriesFromMemoGraph(): Promise<any[]> {
        const operation = async () => {
            const url = `${this.settings.memoGraphUrl}/api/memories`;
            const headers: Record<string, string> = {
                'Content-Type': 'application/json'
            };

            if (this.settings.apiKey) {
                headers['Authorization'] = `Bearer ${this.settings.apiKey}`;
            }

            const response = await fetch(url, {
                method: 'GET',
                headers: headers
            });

            if (!response.ok) {
                throw new Error(`MemoGraph API error: ${response.statusText}`);
            }

            const data = await response.json();
            // Filter for memories that originated from Obsidian or need to be synced
            return data.memories || [];
        };

        return await this.retryWithBackoff(operation, 3, 1000);
    }

    async saveMemoryToVault(memory: any): Promise<void> {
        // Extract path from metadata or generate one
        const filePath = memory.metadata?.path || `${memory.title || memory.id}.md`;

        // Check if file already exists
        const existingFile = this.app.vault.getAbstractFileByPath(filePath);

        // Convert memory to markdown format with frontmatter
        const markdownContent = this.memoryToMarkdown(memory);

        if (existingFile instanceof TFile) {
            // File exists - check for conflicts
            const currentContent = await this.app.vault.read(existingFile);

            if (currentContent !== markdownContent) {
                // Conflict detected
                const resolvedContent = await this.handleConflict(
                    filePath,
                    currentContent,
                    markdownContent,
                    existingFile.stat.mtime,
                    memory.metadata?.modified || Date.now()
                );

                if (resolvedContent !== null) {
                    await this.app.vault.modify(existingFile, resolvedContent);
                }
            }
        } else {
            // File doesn't exist - create it
            // Ensure parent folders exist
            const parentPath = filePath.substring(0, filePath.lastIndexOf('/'));
            if (parentPath && !this.app.vault.getAbstractFileByPath(parentPath)) {
                await this.createFolderPath(parentPath);
            }

            await this.app.vault.create(filePath, markdownContent);
        }
    }

    async handleConflict(
        filePath: string,
        localContent: string,
        remoteContent: string,
        localModified: number,
        remoteModified: number
    ): Promise<string | null> {
        // Check if we should use automatic resolution
        if (this.settings.conflictStrategy !== 'manual') {
            // Automatic resolution based on strategy
            let resolvedContent: string | null = null;
            let resolution: ConflictResolution = 'keep-local';

            switch (this.settings.conflictStrategy) {
                case 'obsidian_wins':
                    resolvedContent = localContent;
                    resolution = 'keep-local';
                    break;
                case 'memograph_wins':
                    resolvedContent = remoteContent;
                    resolution = 'keep-remote';
                    break;
                case 'newest_wins':
                    resolvedContent = localModified > remoteModified ? localContent : remoteContent;
                    resolution = localModified > remoteModified ? 'keep-local' : 'keep-remote';
                    break;
            }

            // Log automatic resolution
            this.conflictHistory.push({
                filePath,
                timestamp: Date.now(),
                resolution,
                autoResolved: true
            });

            new Notice(`Conflict auto-resolved: ${filePath} (${resolution})`);
            return resolvedContent;
        }

        // Manual resolution - show conflict modal
        return new Promise<string | null>((resolve) => {
            const conflictData: ConflictData = {
                filePath,
                localVersion: localContent,
                remoteVersion: remoteContent,
                localModified,
                remoteModified
            };

            const modal = new ConflictModal(
                this.app,
                conflictData,
                (resolution: ConflictResolution, mergedContent?: string) => {
                    let resolvedContent: string | null = null;

                    switch (resolution) {
                        case 'keep-local':
                            resolvedContent = localContent;
                            break;
                        case 'keep-remote':
                            resolvedContent = remoteContent;
                            break;
                        case 'keep-both':
                            resolvedContent = mergedContent || this.createMergedContent(
                                localContent,
                                remoteContent,
                                localModified,
                                remoteModified
                            );
                            break;
                        case 'manual':
                            // User wants to manually edit
                            resolvedContent = this.createMergedContent(
                                localContent,
                                remoteContent,
                                localModified,
                                remoteModified
                            );
                            new Notice('Conflict markers added. Please resolve manually.');
                            break;
                    }

                    // Log manual resolution
                    this.conflictHistory.push({
                        filePath,
                        timestamp: Date.now(),
                        resolution,
                        autoResolved: false
                    });

                    resolve(resolvedContent);
                }
            );

            modal.open();
        });
    }

    createMergedContent(
        localContent: string,
        remoteContent: string,
        localModified: number,
        remoteModified: number
    ): string {
        return `\<<<<<<< Local Version (${new Date(localModified).toLocaleString()})
${localContent}
=======
${remoteContent}
>>>>>>> Remote Version (MemoGraph) (${new Date(remoteModified).toLocaleString()})
`;
    }

    getConflictHistory(): ConflictLog[] {
        return this.conflictHistory;
    }

    clearConflictHistory(): void {
        this.conflictHistory = [];
    }

    memoryToMarkdown(memory: any): string {
        // Build frontmatter
        const frontmatter: Record<string, any> = {
            title: memory.title || memory.metadata?.title || 'Untitled',
            tags: memory.tags || [],
            ...memory.metadata
        };

        // Remove redundant fields
        delete frontmatter.path;
        delete frontmatter.source;

        // Build markdown content
        let markdown = '---\n';
        for (const [key, value] of Object.entries(frontmatter)) {
            if (Array.isArray(value)) {
                markdown += `${key}: [${value.join(', ')}]\n`;
            } else if (typeof value === 'string') {
                markdown += `${key}: ${value}\n`;
            } else {
                markdown += `${key}: ${JSON.stringify(value)}\n`;
            }
        }
        markdown += '---\n\n';
        markdown += memory.content || '';

        return markdown;
    }

    async createFolderPath(path: string): Promise<void> {
        const parts = path.split('/');
        let currentPath = '';

        for (const part of parts) {
            currentPath = currentPath ? `${currentPath}/${part}` : part;
            const folder = this.app.vault.getAbstractFileByPath(currentPath);

            if (!folder) {
                await this.app.vault.createFolder(currentPath);
            }
        }
    }

    filterFiles(files: TFile[]): TFile[] {
        return files.filter(file => {
            // Check excluded folders
            for (const folder of this.settings.excludedFolders) {
                if (file.path.startsWith(folder + '/') || file.path === folder) {
                    return false;
                }
            }

            // Check included tags (if any specified)
            if (this.settings.includedTags.length > 0) {
                const metadata = this.app.metadataCache.getFileCache(file);
                const tags = metadata?.tags?.map(t => t.tag) || [];
                const frontmatterTags = metadata?.frontmatter?.tags || [];
                const allTags = [...tags, ...frontmatterTags];

                // File must have at least one of the included tags
                const hasIncludedTag = this.settings.includedTags.some(includedTag =>
                    allTags.some(tag => tag.includes(includedTag))
                );

                if (!hasIncludedTag) {
                    return false;
                }
            }

            return true;
        });
    }

    getSyncQueueStatus(): { queued: number; syncing: boolean; queuedFiles: string[] } {
        return {
            queued: this.syncQueue.size,
            syncing: this.syncing,
            queuedFiles: Array.from(this.syncQueue)
        };
    }

    cancelAllPendingSyncs(): void {
        // Clear all debounce timers
        for (const timer of this.debounceTimers.values()) {
            clearTimeout(timer);
        }
        this.debounceTimers.clear();
        this.syncQueue.clear();
    }

    /**
     * Retry an operation with exponential backoff
     * @param operation - Async operation to retry
     * @param maxAttempts - Maximum number of retry attempts (default: 3)
     * @param initialDelay - Initial delay in milliseconds (default: 1000)
     * @returns Result of the operation
     */
    async retryWithBackoff<T>(
        operation: () => Promise<T>,
        maxAttempts: number = 3,
        initialDelay: number = 1000
    ): Promise<T> {
        let lastError: Error | null = null;
        let delay = initialDelay;

        for (let attempt = 1; attempt <= maxAttempts; attempt++) {
            try {
                return await operation();
            } catch (error) {
                lastError = error as Error;

                // Record error
                this.recordError(lastError, attempt < maxAttempts);

                // Check if error is retryable
                if (!this.isRetryableError(lastError)) {
                    throw lastError;
                }

                // Don't wait after the last attempt
                if (attempt < maxAttempts) {
                    await this.sleep(delay);
                    delay *= 2; // Exponential backoff
                }
            }
        }

        // All retries exhausted
        throw lastError;
    }

    /**
     * Check if an error is retryable (transient)
     * @param error - Error to check
     * @returns True if error is retryable
     */
    private isRetryableError(error: Error): boolean {
        const message = error.message.toLowerCase();

        // Network errors
        if (message.includes('network') ||
            message.includes('timeout') ||
            message.includes('connection') ||
            message.includes('econnrefused') ||
            message.includes('enotfound')) {
            return true;
        }

        // HTTP status codes that are retryable
        if (message.includes('503') || // Service Unavailable
            message.includes('504') || // Gateway Timeout
            message.includes('429')) { // Too Many Requests
            return true;
        }

        return false;
    }

    /**
     * Sleep for a specified duration
     * @param ms - Duration in milliseconds
     */
    private sleep(ms: number): Promise<void> {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    /**
     * Record an error in the error history
     * @param error - Error to record
     * @param willRetry - Whether the operation will be retried
     */
    private recordError(error: Error, willRetry: boolean): void {
        const errorEntry = {
            timestamp: Date.now(),
            message: error.message,
            type: error.name,
            willRetry
        };

        this.errorHistory.push(errorEntry);

        // Keep only last 100 errors
        if (this.errorHistory.length > 100) {
            this.errorHistory = this.errorHistory.slice(-100);
        }

        // Log to console for debugging
        if (willRetry) {
            console.warn(`Sync error (will retry): ${error.message}`);
        } else {
            console.error(`Sync error (permanent): ${error.message}`);
        }
    }

    /**
     * Get error history
     * @returns Array of error entries
     */
    getErrorHistory(): Array<{timestamp: number; message: string; type: string}> {
        return [...this.errorHistory];
    }

    /**
     * Clear error history
     * @returns Number of errors cleared
     */
    clearErrorHistory(): number {
        const count = this.errorHistory.length;
        this.errorHistory = [];
        return count;
    }
}
