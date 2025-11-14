/**
 * Language store (Zustand store for language and auto-detection).
 *
 * Overview
 *   Manages global language state including current language, auto-detection
 *   preference, and detected language. Persists preferences to localStorage
 *   and synchronizes with backend API.
 *
 * Design
 *   - **State Management**: Uses Zustand for global state.
 *   - **Persistence**: Persists language and autoDetect to localStorage.
 *   - **Auto-Detection**: Detects language from IP geolocation and browser.
 *   - **Backend Sync**: Synchronizes with backend API (TODO).
 *
 * Integration
 *   - Consumes: None (manages own state, uses browser APIs).
 *   - Returns: Zustand store hook (useLanguageStore).
 *   - Used by: LanguageSelector and language-aware components.
 *   - Observability: N/A (state management only).
 *
 * Usage
 *   >>> const { language, setLanguage, detectLanguage } = useLanguageStore();
 *   >>> await detectLanguage();
 *   >>> setLanguage("en-US");
 */

"use client";

import { create } from "zustand";
import { persist } from "zustand/middleware";
import i18n from "@/lib/i18n/config";
import { detectLanguage as detectLanguageUtil } from "@/lib/i18n/detector";

interface LanguageState {
  // State
  language: string;
  autoDetect: boolean;
  detectedLanguage: string | null;

  // Actions
  setLanguage: (language: string) => void;
  setAutoDetect: (autoDetect: boolean) => void;
  detectLanguage: () => Promise<void>;
  loadLanguage: () => Promise<void>;
  saveLanguage: () => Promise<void>;
}

const DEFAULT_LANGUAGE = "pt-BR";
const STORAGE_KEY = "language-store";

export const useLanguageStore = create<LanguageState>()(
  persist(
    (set, get) => ({
      // Initial state
      language: DEFAULT_LANGUAGE,
      autoDetect: true,
      detectedLanguage: null,

      // Actions
      setLanguage: (language: string) => {
        set({ language });
        // Update i18next language
        i18n.changeLanguage(language);
        get().saveLanguage();
      },

      setAutoDetect: (autoDetect: boolean) => {
        set({ autoDetect });
        if (autoDetect) {
          get().detectLanguage();
        }
        get().saveLanguage();
      },

      detectLanguage: async () => {
        try {
          // Use detector utility (IP geolocation + browser)
          const detectedLang = await detectLanguageUtil();

          set({
            detectedLanguage: detectedLang,
            language: get().autoDetect ? detectedLang : get().language,
          });

          // Update i18next if auto-detect is enabled
          if (get().autoDetect) {
            i18n.changeLanguage(detectedLang);
          }
        } catch (error) {
          console.error("Failed to detect language:", error);
          set({
            detectedLanguage: DEFAULT_LANGUAGE,
            language: get().autoDetect ? DEFAULT_LANGUAGE : get().language,
          });

          // Update i18next to default if auto-detect is enabled
          if (get().autoDetect) {
            i18n.changeLanguage(DEFAULT_LANGUAGE);
          }
        }
      },

      loadLanguage: async () => {
        // Load from localStorage (handled by persist middleware)
        // TODO: Load from backend API
        try {
          const saved = localStorage.getItem(STORAGE_KEY);
          if (saved) {
            const parsed = JSON.parse(saved);
            if (parsed.state) {
              const loadedLanguage = parsed.state.language || DEFAULT_LANGUAGE;
              set(parsed.state);
              // Update i18next with loaded language
              i18n.changeLanguage(loadedLanguage);
            }
          } else {
            // No saved language, use i18next detected language or default
            const i18nLanguage = i18n.language || DEFAULT_LANGUAGE;
            set({ language: i18nLanguage });
            i18n.changeLanguage(i18nLanguage);
          }

          // Auto-detect if enabled
          if (get().autoDetect && !get().detectedLanguage) {
            await get().detectLanguage();
          } else if (!get().autoDetect) {
            // Ensure i18next matches store language
            i18n.changeLanguage(get().language);
          }
        } catch (error) {
          console.error("Failed to load language:", error);
          // Fallback to default
          set({ language: DEFAULT_LANGUAGE });
          i18n.changeLanguage(DEFAULT_LANGUAGE);
        }
      },

      saveLanguage: async () => {
        // Save to localStorage (handled by persist middleware)
        // TODO: Sync with backend API
        try {
          const state = get();
          const languageToSave = {
            language: state.language,
            autoDetect: state.autoDetect,
          };

          // TODO: Sync with backend API
          // await fetch("/api/v1/user/preferences", {
          //   method: "PUT",
          //   body: JSON.stringify(languageToSave),
          // });
        } catch (error) {
          console.error("Failed to save language:", error);
        }
      },
    }),
    {
      name: STORAGE_KEY,
      partialize: (state) => ({
        language: state.language,
        autoDetect: state.autoDetect,
        // Don't persist detectedLanguage (re-detect on load)
      }),
    }
  )
);

