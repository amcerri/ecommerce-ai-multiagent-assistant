/**
 * i18next configuration (internationalization setup).
 *
 * Overview
 *   Configures i18next with multiple languages, namespaces, and automatic
 *   language detection. Supports pt-BR, en-US, es-ES, fr-FR, and de-DE.
 *
 * Design
 *   - **Languages**: pt-BR (default), en-US, es-ES, fr-FR, de-DE
 *   - **Namespaces**: common, chat
 *   - **Detection**: localStorage → browser language → IP geolocation → pt-BR
 *   - **Fallback**: Always falls back to pt-BR if detection fails
 *   - **Interpolation**: Enabled for dynamic values
 *   - **Pluralization**: Enabled for proper plural forms
 *
 * Integration
 *   - Consumes: i18next, i18next-browser-languagedetector
 *   - Returns: Configured i18next instance
 *   - Used by: All components via useTranslation hook
 *   - Observability: N/A (configuration only)
 *
 * Usage
 *   >>> import i18n from "@/lib/i18n/config";
 *   >>> await i18n.init();
 *   >>> const { t } = useTranslation();
 *   >>> t("common:app.name")
 */

import i18n from "i18next";
import { initReactI18next } from "react-i18next";
import LanguageDetector from "i18next-browser-languagedetector";

import ptBRCommon from "@/locales/pt-BR/common.json";
import ptBRChat from "@/locales/pt-BR/chat.json";
import enUSCommon from "@/locales/en-US/common.json";
import enUSChat from "@/locales/en-US/chat.json";
import esESCommon from "@/locales/es-ES/common.json";
import esESChat from "@/locales/es-ES/chat.json";
import frFRCommon from "@/locales/fr-FR/common.json";
import frFRChat from "@/locales/fr-FR/chat.json";
import deDECommon from "@/locales/de-DE/common.json";
import deDEChat from "@/locales/de-DE/chat.json";

const resources = {
  "pt-BR": {
    common: ptBRCommon,
    chat: ptBRChat,
  },
  "en-US": {
    common: enUSCommon,
    chat: enUSChat,
  },
  "es-ES": {
    common: esESCommon,
    chat: esESChat,
  },
  "fr-FR": {
    common: frFRCommon,
    chat: frFRChat,
  },
  "de-DE": {
    common: deDECommon,
    chat: deDEChat,
  },
};

const detectionOptions = {
  // Order of detection
  order: ["localStorage", "navigator", "htmlTag"],
  
  // Keys to lookup language from
  lookupLocalStorage: "language-store",
  
  // Cache user language
  caches: ["localStorage"],
  
  // Only detect language, don't change it automatically
  checkWhitelist: true,
};

i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources,
    fallbackLng: "pt-BR",
    defaultNS: "common",
    ns: ["common", "chat"],
    
    // Detection options
    detection: detectionOptions,
    
    // Interpolation options
    interpolation: {
      escapeValue: false, // React already escapes values
    },
    
    // React options
    react: {
      useSuspense: false, // Disable suspense for better compatibility
    },
    
    // Debug (disable in production)
    debug: typeof process !== "undefined" && process.env?.NODE_ENV === "development",
  });

export default i18n;

