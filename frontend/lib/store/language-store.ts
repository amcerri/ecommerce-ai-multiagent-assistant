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
          // Try IP geolocation first (geojs.io - free, no API key)
          let detectedLang: string | null = null;

          try {
            const geoResponse = await fetch("https://get.geojs.io/v1/ip/country.json");
            if (geoResponse.ok) {
              const geoData = await geoResponse.json();
              const country = geoData.country?.toLowerCase();

              // Map country to language
              if (country === "br") {
                detectedLang = "pt-BR";
              } else if (country === "us" || country === "gb" || country === "ca" || country === "au") {
                detectedLang = "en-US";
              } else if (country === "es" || country === "mx" || country === "ar") {
                detectedLang = "es-ES";
              } else if (country === "fr") {
                detectedLang = "fr-FR";
              } else if (country === "de" || country === "at" || country === "ch") {
                detectedLang = "de-DE";
              }
            }
          } catch (error) {
            console.warn("IP geolocation failed, trying browser language:", error);
          }

          // Fallback to browser language
          if (!detectedLang) {
            const browserLang = navigator.language || (navigator as any).userLanguage;
            if (browserLang) {
              if (browserLang.startsWith("pt")) {
                detectedLang = "pt-BR";
              } else if (browserLang.startsWith("en")) {
                detectedLang = "en-US";
              } else if (browserLang.startsWith("es")) {
                detectedLang = "es-ES";
              } else if (browserLang.startsWith("fr")) {
                detectedLang = "fr-FR";
              } else if (browserLang.startsWith("de")) {
                detectedLang = "de-DE";
              }
            }
          }

          // Final fallback to default
          if (!detectedLang) {
            detectedLang = DEFAULT_LANGUAGE;
          }

          set({
            detectedLanguage: detectedLang,
            language: get().autoDetect ? detectedLang : get().language,
          });
        } catch (error) {
          console.error("Failed to detect language:", error);
          set({
            detectedLanguage: DEFAULT_LANGUAGE,
            language: get().autoDetect ? DEFAULT_LANGUAGE : get().language,
          });
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
              set(parsed.state);
            }
          }

          // Auto-detect if enabled
          if (get().autoDetect && !get().detectedLanguage) {
            await get().detectLanguage();
          }
        } catch (error) {
          console.error("Failed to load language:", error);
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

