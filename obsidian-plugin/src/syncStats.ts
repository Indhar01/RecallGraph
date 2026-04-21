/**
 * Sync statistics tracking and management
 */

export interface SyncStatistics {
    totalSyncs: number;
    lastSyncTime: number | null;
    successfulSyncs: number;
    failedSyncs: number;
    filesPulled: number;
    filesPushed: number;
    conflictsResolved: number;
    totalErrors: number;
    averageSyncDuration: number;
    lastSyncDuration: number;
    lastSyncStats: {
        pulled: number;
        pushed: number;
        conflicts: number;
        errors: string[];
        timestamp: number;
        duration: number;
    } | null;
}

export interface SyncHistoryEntry {
    timestamp: number;
    direction: 'pull' | 'push' | 'bidirectional';
    pulled: number;
    pushed: number;
    conflicts: number;
    errors: string[];
    duration: number;
    status: 'success' | 'failed' | 'cancelled';
}

export class SyncStatsManager {
    private stats: SyncStatistics;
    private history: SyncHistoryEntry[];
    private maxHistorySize: number;
    private storageKey: string;

    constructor(storageKey: string = 'memograph-sync-stats', maxHistorySize: number = 50) {
        this.storageKey = storageKey;
        this.maxHistorySize = maxHistorySize;
        this.stats = this.getDefaultStats();
        this.history = [];
        this.loadFromStorage();
    }

    private getDefaultStats(): SyncStatistics {
        return {
            totalSyncs: 0,
            lastSyncTime: null,
            successfulSyncs: 0,
            failedSyncs: 0,
            filesPulled: 0,
            filesPushed: 0,
            conflictsResolved: 0,
            totalErrors: 0,
            averageSyncDuration: 0,
            lastSyncDuration: 0,
            lastSyncStats: null
        };
    }

    recordSyncStart(direction: 'pull' | 'push' | 'bidirectional'): number {
        return Date.now();
    }

    recordSyncEnd(
        startTime: number,
        direction: 'pull' | 'push' | 'bidirectional',
        pulled: number,
        pushed: number,
        conflicts: number,
        errors: string[],
        cancelled: boolean = false
    ): void {
        const endTime = Date.now();
        const duration = endTime - startTime;
        const status: 'success' | 'failed' | 'cancelled' = 
            cancelled ? 'cancelled' : (errors.length > 0 ? 'failed' : 'success');

        // Update statistics
        this.stats.totalSyncs++;
        this.stats.lastSyncTime = endTime;
        this.stats.lastSyncDuration = duration;
        this.stats.filesPulled += pulled;
        this.stats.filesPushed += pushed;
        this.stats.conflictsResolved += conflicts;
        this.stats.totalErrors += errors.length;

        if (status === 'success') {
            this.stats.successfulSyncs++;
        } else if (status === 'failed') {
            this.stats.failedSyncs++;
        }

        // Update average sync duration
        this.stats.averageSyncDuration = 
            (this.stats.averageSyncDuration * (this.stats.totalSyncs - 1) + duration) / 
            this.stats.totalSyncs;

        // Store last sync details
        this.stats.lastSyncStats = {
            pulled,
            pushed,
            conflicts,
            errors,
            timestamp: endTime,
            duration
        };

        // Add to history
        const historyEntry: SyncHistoryEntry = {
            timestamp: endTime,
            direction,
            pulled,
            pushed,
            conflicts,
            errors,
            duration,
            status
        };
        
        this.history.unshift(historyEntry);
        
        // Trim history if needed
        if (this.history.length > this.maxHistorySize) {
            this.history = this.history.slice(0, this.maxHistorySize);
        }

        this.saveToStorage();
    }

    getStatistics(): SyncStatistics {
        return { ...this.stats };
    }

    getHistory(limit?: number): SyncHistoryEntry[] {
        if (limit) {
            return this.history.slice(0, limit);
        }
        return [...this.history];
    }

    getRecentErrors(limit: number = 10): string[] {
        const errors: string[] = [];
        for (const entry of this.history) {
            if (entry.errors.length > 0) {
                errors.push(...entry.errors.map(e => `[${new Date(entry.timestamp).toLocaleString()}] ${e}`));
                if (errors.length >= limit) {
                    break;
                }
            }
        }
        return errors.slice(0, limit);
    }

    clearHistory(): void {
        this.history = [];
        this.saveToStorage();
    }

    resetStatistics(): void {
        this.stats = this.getDefaultStats();
        this.history = [];
        this.saveToStorage();
    }

    private loadFromStorage(): void {
        try {
            const stored = localStorage.getItem(this.storageKey);
            if (stored) {
                const data = JSON.parse(stored);
                this.stats = data.stats || this.getDefaultStats();
                this.history = data.history || [];
            }
        } catch (error) {
            console.error('Failed to load sync stats from storage:', error);
        }
    }

    private saveToStorage(): void {
        try {
            const data = {
                stats: this.stats,
                history: this.history
            };
            localStorage.setItem(this.storageKey, JSON.stringify(data));
        } catch (error) {
            console.error('Failed to save sync stats to storage:', error);
        }
    }

    getSuccessRate(): number {
        if (this.stats.totalSyncs === 0) return 0;
        return (this.stats.successfulSyncs / this.stats.totalSyncs) * 100;
    }

    getAverageFilesPerSync(): { pulled: number; pushed: number } {
        if (this.stats.totalSyncs === 0) {
            return { pulled: 0, pushed: 0 };
        }
        return {
            pulled: this.stats.filesPulled / this.stats.totalSyncs,
            pushed: this.stats.filesPushed / this.stats.totalSyncs
        };
    }

    formatDuration(ms: number): string {
        if (ms < 1000) return `${ms}ms`;
        if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
        const minutes = Math.floor(ms / 60000);
        const seconds = ((ms % 60000) / 1000).toFixed(0);
        return `${minutes}m ${seconds}s`;
    }
}