/**
 * Settings store (Zustand store for display preferences).
 *
 * Overview
 *   Manages global settings for display preferences including metadata visibility,
 *   formatting options, and behavior settings. Persists all settings to localStorage
 *   and synchronizes with backend API.
 *
 * Design
 *   - **State Management**: Uses Zustand for global state.
 *   - **Persistence**: Persists all settings to localStorage.
 *   - **Backend Sync**: Synchronizes with backend API (TODO).
 *   - **Actions**: Update settings, reset to defaults, load/save.
 *
 * Integration
 *   - Consumes: None (manages own state).
 *   - Returns: Zustand store hook (useSettingsStore).
 *   - Used by: SettingsPanel and display components.
 *   - Observability: N/A (state management only).
 *
 * Usage
 *   >>> const { showMetadata, updateSetting } = useSettingsStore();
 *   >>> updateSetting("showMetadata", true);
 */

"use client";

import { create } from "zustand";
import { persist } from "zustand/middleware";

interface SettingsState {
  // Metadata Display
  showMetadata: boolean;
  showSQL: boolean;
  showChunks: boolean;
  showSimilarityScores: boolean;
  showPerformanceMetrics: boolean;
  highlightCitations: boolean;
  showCitationTooltips: boolean;

  // Formatting
  formatCode: boolean;
  syntaxHighlighting: boolean;
  formatNumbers: boolean;
  relativeDates: boolean;

  // Behavior
  autoScroll: boolean;
  notificationSound: boolean;
  confirmSQLExecution: boolean;

  // Actions
  updateSetting: <K extends keyof Omit<SettingsState, "updateSetting" | "resetSettings" | "loadSettings" | "saveSettings">>(
    key: K,
    value: SettingsState[K]
  ) => void;
  resetSettings: () => void;
  loadSettings: () => Promise<void>;
  saveSettings: () => Promise<void>;
}

const DEFAULT_SETTINGS: Omit<SettingsState, "updateSetting" | "resetSettings" | "loadSettings" | "saveSettings"> = {
  showMetadata: true,
  showSQL: true,
  showChunks: true,
  showSimilarityScores: true,
  showPerformanceMetrics: false,
  highlightCitations: true,
  showCitationTooltips: true,
  formatCode: true,
  syntaxHighlighting: true,
  formatNumbers: true,
  relativeDates: true,
  autoScroll: true,
  notificationSound: false,
  confirmSQLExecution: true,
};

const STORAGE_KEY = "settings-store";

export const useSettingsStore = create<SettingsState>()(
  persist(
    (set, get) => ({
      // Initial state (defaults)
      ...DEFAULT_SETTINGS,

      // Actions
      updateSetting: <K extends keyof Omit<SettingsState, "updateSetting" | "resetSettings" | "loadSettings" | "saveSettings">>(
        key: K,
        value: SettingsState[K]
      ) => {
        set({ [key]: value } as Partial<SettingsState>);
        // Auto-save after update
        get().saveSettings();
      },

      resetSettings: () => {
        set(DEFAULT_SETTINGS);
        get().saveSettings();
      },

      loadSettings: async () => {
        // Load from localStorage (handled by persist middleware)
        // TODO: Load from backend API
        try {
          const saved = localStorage.getItem(STORAGE_KEY);
          if (saved) {
            const parsed = JSON.parse(saved);
            if (parsed.state) {
              set(parsed.state);
            }
          }
        } catch (error) {
          console.error("Failed to load settings:", error);
        }
      },

      saveSettings: async () => {
        // Save to localStorage (handled by persist middleware)
        // TODO: Sync with backend API
        try {
          const state = get();
          const settingsToSave = {
            showMetadata: state.showMetadata,
            showSQL: state.showSQL,
            showChunks: state.showChunks,
            showSimilarityScores: state.showSimilarityScores,
            showPerformanceMetrics: state.showPerformanceMetrics,
            highlightCitations: state.highlightCitations,
            showCitationTooltips: state.showCitationTooltips,
            formatCode: state.formatCode,
            syntaxHighlighting: state.syntaxHighlighting,
            formatNumbers: state.formatNumbers,
            relativeDates: state.relativeDates,
            autoScroll: state.autoScroll,
            notificationSound: state.notificationSound,
            confirmSQLExecution: state.confirmSQLExecution,
          };

          // TODO: Sync with backend API
          // await fetch("/api/v1/user/settings", {
          //   method: "PUT",
          //   body: JSON.stringify(settingsToSave),
          // });
        } catch (error) {
          console.error("Failed to save settings:", error);
        }
      },
    }),
    {
      name: STORAGE_KEY,
      // Persist all settings
      partialize: (state) => ({
        showMetadata: state.showMetadata,
        showSQL: state.showSQL,
        showChunks: state.showChunks,
        showSimilarityScores: state.showSimilarityScores,
        showPerformanceMetrics: state.showPerformanceMetrics,
        highlightCitations: state.highlightCitations,
        showCitationTooltips: state.showCitationTooltips,
        formatCode: state.formatCode,
        syntaxHighlighting: state.syntaxHighlighting,
        formatNumbers: state.formatNumbers,
        relativeDates: state.relativeDates,
        autoScroll: state.autoScroll,
        notificationSound: state.notificationSound,
        confirmSQLExecution: state.confirmSQLExecution,
      }),
    }
  )
);

