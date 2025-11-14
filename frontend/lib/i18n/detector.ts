/**
 * Language detection utilities (IP geolocation and browser detection).
 *
 * Overview
 *   Provides functions to detect user language from IP geolocation and
 *   browser settings. Uses free APIs (geojs.io, ip-api.com) with graceful
 *   degradation if APIs fail.
 *
 * Design
 *   - **IP Geolocation**: Uses geojs.io (primary) and ip-api.com (fallback)
 *   - **Browser Detection**: Uses navigator.language
 *   - **Country Mapping**: Maps country codes to language codes
 *   - **Graceful Degradation**: Always returns valid language (pt-BR fallback)
 *   - **Error Handling**: Catches and logs errors, never throws
 *
 * Integration
 *   - Consumes: Browser fetch API, navigator.language
 *   - Returns: Language codes (pt-BR, en-US, es-ES, fr-FR, de-DE)
 *   - Used by: LanguageStore for automatic language detection
 *   - Observability: Logs warnings on API failures
 *
 * Usage
 *   >>> import { detectLanguage } from "@/lib/i18n/detector";
 *   >>> const language = await detectLanguage();
 *   >>> // Returns: "pt-BR" | "en-US" | "es-ES" | "fr-FR" | "de-DE"
 */

/**
 * Maps country code to language code.
 *
 * @param country - Two-letter country code (lowercase).
 * @returns Language code or null if no mapping exists.
 */
function mapCountryToLanguage(country: string): string | null {
  const countryMap: Record<string, string> = {
    // Portuguese
    br: "pt-BR", // Brazil
    pt: "pt-BR", // Portugal
    
    // English
    us: "en-US", // United States
    gb: "en-US", // United Kingdom
    ca: "en-US", // Canada
    au: "en-US", // Australia
    nz: "en-US", // New Zealand
    ie: "en-US", // Ireland
    
    // Spanish
    es: "es-ES", // Spain
    mx: "es-ES", // Mexico
    ar: "es-ES", // Argentina
    co: "es-ES", // Colombia
    cl: "es-ES", // Chile
    pe: "es-ES", // Peru
    
    // French
    fr: "fr-FR", // France
    be: "fr-FR", // Belgium (French-speaking)
    ch: "fr-FR", // Switzerland (French-speaking)
    ca: "fr-FR", // Canada (French-speaking regions)
    
    // German
    de: "de-DE", // Germany
    at: "de-DE", // Austria
    ch: "de-DE", // Switzerland (German-speaking)
  };
  
  return countryMap[country.toLowerCase()] || null;
}

/**
 * Detects language from IP geolocation.
 *
 * Uses free APIs (geojs.io as primary, ip-api.com as fallback) to detect
 * user's country and map it to a language code.
 *
 * @returns Language code or null if detection fails.
 */
export async function detectLanguageFromIP(): Promise<string | null> {
  try {
    // Try geojs.io first (free, no API key required)
    try {
      const response = await fetch("https://get.geojs.io/v1/ip/country.json", {
        method: "GET",
        headers: {
          Accept: "application/json",
        },
        // Timeout after 3 seconds
        signal: AbortSignal.timeout(3000),
      });
      
      if (response.ok) {
        const data = await response.json();
        const country = data.country;
        
        if (country) {
          const language = mapCountryToLanguage(country);
          if (language) {
            return language;
          }
        }
      }
    } catch (error) {
      console.warn("geojs.io failed, trying fallback:", error);
    }
    
    // Fallback to ip-api.com (free, no API key required)
    try {
      const response = await fetch("http://ip-api.com/json/?fields=countryCode", {
        method: "GET",
        headers: {
          Accept: "application/json",
        },
        // Timeout after 3 seconds
        signal: AbortSignal.timeout(3000),
      });
      
      if (response.ok) {
        const data = await response.json();
        const countryCode = data.countryCode;
        
        if (countryCode) {
          const language = mapCountryToLanguage(countryCode);
          if (language) {
            return language;
          }
        }
      }
    } catch (error) {
      console.warn("ip-api.com failed:", error);
    }
    
    return null;
  } catch (error) {
    console.warn("IP geolocation detection failed:", error);
    return null;
  }
}

/**
 * Detects language from browser settings.
 *
 * Uses navigator.language to detect user's preferred browser language
 * and normalizes it to a supported language code.
 *
 * @returns Language code or null if detection fails.
 */
export function detectLanguageFromBrowser(): string | null {
  try {
    const browserLang = navigator.language || (navigator as any).userLanguage;
    
    if (!browserLang) {
      return null;
    }
    
    // Normalize language code (e.g., "pt" -> "pt-BR", "en" -> "en-US")
    const langCode = browserLang.toLowerCase();
    
    if (langCode.startsWith("pt")) {
      return "pt-BR";
    } else if (langCode.startsWith("en")) {
      return "en-US";
    } else if (langCode.startsWith("es")) {
      return "es-ES";
    } else if (langCode.startsWith("fr")) {
      return "fr-FR";
    } else if (langCode.startsWith("de")) {
      return "de-DE";
    }
    
    return null;
  } catch (error) {
    console.warn("Browser language detection failed:", error);
    return null;
  }
}

/**
 * Detects language using all available sources.
 *
 * Tries IP geolocation first, then browser language, and finally
 * falls back to pt-BR if all detection methods fail.
 *
 * @returns Language code (always returns a valid language).
 */
export async function detectLanguage(): Promise<string> {
  const DEFAULT_LANGUAGE = "pt-BR";
  
  // Try IP geolocation first
  const ipLanguage = await detectLanguageFromIP();
  if (ipLanguage) {
    return ipLanguage;
  }
  
  // Fallback to browser language
  const browserLanguage = detectLanguageFromBrowser();
  if (browserLanguage) {
    return browserLanguage;
  }
  
  // Final fallback to default
  return DEFAULT_LANGUAGE;
}

