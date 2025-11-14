/**
 * i18next provider component (initializes i18next on client side).
 *
 * Overview
 *   Client component that initializes i18next and loads language preferences
 *   from LanguageStore. Must be used in the root layout to enable i18n
 *   throughout the application.
 *
 * Design
 *   - **Initialization**: Initializes i18next on mount
 *   - **Language Loading**: Loads language from LanguageStore
 *   - **Auto-Detection**: Triggers auto-detection if enabled
 *   - **Suspense**: Uses Suspense boundary for loading state
 *
 * Integration
 *   - Consumes: i18next config, LanguageStore
 *   - Returns: React component wrapper
 *   - Used by: Root layout (app/layout.tsx)
 *   - Observability: N/A (initialization only)
 *
 * Usage
 *   >>> import { I18nProvider } from "@/lib/i18n/provider";
 *   >>> <I18nProvider>{children}</I18nProvider>
 */

"use client";

import { useEffect, Suspense, type ReactNode } from "react";
import { useLanguageStore } from "@/lib/store";
import "@/lib/i18n/config";

interface I18nProviderProps {
  children: ReactNode;
}

export function I18nProvider({ children }: I18nProviderProps) {
  const { loadLanguage } = useLanguageStore();

  useEffect(() => {
    // Load language preferences on mount
    loadLanguage();
  }, [loadLanguage]);

  return <Suspense fallback={<div>Loading...</div>}>{children}</Suspense>;
}

