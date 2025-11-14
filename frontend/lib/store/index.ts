/**
 * Store exports (centralized exports for all Zustand stores).
 *
 * Overview
 *   Provides centralized exports for all Zustand stores used in the application.
 *   Simplifies imports and ensures consistent usage across components.
 *
 * Design
 *   - **Centralized Exports**: All stores exported from single location.
 *   - **Type Safety**: Full TypeScript type exports.
 *   - **Organization**: Clear separation of concerns.
 *
 * Integration
 *   - Consumes: All store implementations.
 *   - Returns: Store hooks for use in components.
 *   - Used by: All components that need global state.
 *   - Observability: N/A (exports only).
 *
 * Usage
 *   >>> import { useChatStore, useSettingsStore, useLanguageStore } from "@/lib/store";
 *   >>> const { messages, addMessage } = useChatStore();
 */

export { useChatStore } from "./chat-store";
export { useSettingsStore } from "./settings-store";
export { useLanguageStore } from "./language-store";

