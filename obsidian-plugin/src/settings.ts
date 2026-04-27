import { App, PluginSettingTab, Setting } from 'obsidian';
import MemoGraphPlugin from './main';

export interface MemoGraphSettings {
    memoGraphUrl: string;
    apiKey: string;
    autoSync: boolean;
    syncInterval: number;
    debounceDelay: number;
    conflictStrategy: 'obsidian_wins' | 'memograph_wins' | 'newest_wins' | 'manual';
    excludedFolders: string[];
    includedTags: string[];
}

export const DEFAULT_SETTINGS: MemoGraphSettings = {
    memoGraphUrl: 'http://localhost:5000',
    apiKey: '',
    autoSync: false,
    syncInterval: 300,
    debounceDelay: 300,
    conflictStrategy: 'newest_wins',
    excludedFolders: ['.obsidian', '.trash'],
    includedTags: []
};

export class MemoGraphSettingTab extends PluginSettingTab {
    plugin: MemoGraphPlugin;

    constructor(app: App, plugin: MemoGraphPlugin) {
        super(app, plugin);
        this.plugin = plugin;
    }

    display(): void {
        const {containerEl} = this;

        containerEl.empty();

        containerEl.createEl('h2', {text: 'MemoGraph Sync Settings'});

        new Setting(containerEl)
            .setName('MemoGraph URL')
            .setDesc('URL of your MemoGraph server')
            .addText(text => text
                .setPlaceholder('http://localhost:5000')
                .setValue(this.plugin.settings.memoGraphUrl)
                .onChange(async (value) => {
                    this.plugin.settings.memoGraphUrl = value;
                    await this.plugin.saveSettings();
                }));

        new Setting(containerEl)
            .setName('API Key')
            .setDesc('API key for authentication (optional)')
            .addText(text => text
                .setPlaceholder('Enter your API key')
                .setValue(this.plugin.settings.apiKey)
                .onChange(async (value) => {
                    this.plugin.settings.apiKey = value;
                    await this.plugin.saveSettings();
                }));

        new Setting(containerEl)
            .setName('Auto Sync')
            .setDesc('Automatically sync changes')
            .addToggle(toggle => toggle
                .setValue(this.plugin.settings.autoSync)
                .onChange(async (value) => {
                    this.plugin.settings.autoSync = value;
                    await this.plugin.saveSettings();
                }));

        new Setting(containerEl)
            .setName('Sync Interval')
            .setDesc('Seconds between automatic syncs (if enabled)')
            .addText(text => text
                .setPlaceholder('300')
                .setValue(String(this.plugin.settings.syncInterval))
                .onChange(async (value) => {
                    const num = Number(value);
                    if (!isNaN(num) && num > 0) {
                        this.plugin.settings.syncInterval = num;
                        await this.plugin.saveSettings();
                    }
                }));

        new Setting(containerEl)
            .setName('Debounce Delay')
            .setDesc('Milliseconds to wait after file changes before syncing (prevents sync storms)')
            .addText(text => text
                .setPlaceholder('300')
                .setValue(String(this.plugin.settings.debounceDelay))
                .onChange(async (value) => {
                    const num = Number(value);
                    if (!isNaN(num) && num >= 0) {
                        this.plugin.settings.debounceDelay = num;
                        await this.plugin.saveSettings();
                    }
                }));

        new Setting(containerEl)
            .setName('Conflict Strategy')
            .setDesc('How to resolve sync conflicts')
            .addDropdown(dropdown => dropdown
                .addOption('obsidian_wins', 'Obsidian Wins')
                .addOption('memograph_wins', 'MemoGraph Wins')
                .addOption('newest_wins', 'Newest Wins')
                .addOption('manual', 'Manual Resolution')
                .setValue(this.plugin.settings.conflictStrategy)
                .onChange(async (value) => {
                    this.plugin.settings.conflictStrategy = value as any;
                    await this.plugin.saveSettings();
                }));

        new Setting(containerEl)
            .setName('Excluded Folders')
            .setDesc('Folders to exclude from sync (comma-separated)')
            .addText(text => text
                .setPlaceholder('.obsidian, .trash')
                .setValue(this.plugin.settings.excludedFolders.join(', '))
                .onChange(async (value) => {
                    this.plugin.settings.excludedFolders = value
                        .split(',')
                        .map(f => f.trim())
                        .filter(f => f.length > 0);
                    await this.plugin.saveSettings();
                }));

        new Setting(containerEl)
            .setName('Included Tags')
            .setDesc('Only sync notes with these tags (comma-separated, empty = sync all)')
            .addText(text => text
                .setPlaceholder('memograph, sync')
                .setValue(this.plugin.settings.includedTags.join(', '))
                .onChange(async (value) => {
                    this.plugin.settings.includedTags = value
                        .split(',')
                        .map(t => t.trim())
                        .filter(t => t.length > 0);
                    await this.plugin.saveSettings();
                }));
    }
}
