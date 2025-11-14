/**
 * Settings panel component (display preferences and configuration).
 *
 * Overview
 *   Provides a dialog panel for configuring display preferences. Includes
 *   toggles for metadata visibility, formatting options, and behavior settings.
 *   Persists preferences to localStorage and syncs with backend.
 *
 * Design
 *   - **Dialog**: Uses shadcn/ui Dialog component.
 *   - **Toggles**: Uses shadcn/ui Switch for boolean preferences.
 *   - **Persistence**: Saves to localStorage and syncs with backend API.
 *   - **Sections**: Organized into logical groups.
 *
 * Integration
 *   - Consumes: None (manages own state).
 *   - Returns: Rendered settings dialog.
 *   - Used by: ChatInterface or Header component.
 *   - Observability: N/A (presentation only).
 *
 * Usage
 *   >>> <SettingsPanel open={isOpen} onOpenChange={setIsOpen} />
 */

"use client";

import { useState, useEffect } from "react";
import { Settings } from "lucide-react";

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { Separator } from "@/components/ui/separator";
import { Label } from "@/components/ui/label";

interface SettingsPanelProps {
  open?: boolean;
  onOpenChange?: (open: boolean) => void;
}

interface SettingsState {
  // Metadata Display
  showMetadata: boolean;
  showSql: boolean;
  showChunks: boolean;
  showScores: boolean;
  showMetrics: boolean;
  highlightCitations: boolean;

  // Formatting
  formatCode: boolean;
  syntaxHighlighting: boolean;
  formatNumbers: boolean;
  formatDates: boolean;

  // Behavior
  autoScroll: boolean;
  notifications: boolean;
  confirmations: boolean;
}

const DEFAULT_SETTINGS: SettingsState = {
  showMetadata: true,
  showSql: true,
  showChunks: true,
  showScores: true,
  showMetrics: false,
  highlightCitations: true,
  formatCode: true,
  syntaxHighlighting: true,
  formatNumbers: true,
  formatDates: true,
  autoScroll: true,
  notifications: true,
  confirmations: true,
};

export function SettingsPanel({
  open: controlledOpen,
  onOpenChange: controlledOnOpenChange,
}: SettingsPanelProps) {
  const [internalOpen, setInternalOpen] = useState(false);
  const [settings, setSettings] = useState<SettingsState>(DEFAULT_SETTINGS);

  const isControlled = controlledOpen !== undefined;
  const open = isControlled ? controlledOpen : internalOpen;
  const setOpen = isControlled ? controlledOnOpenChange || (() => {}) : setInternalOpen;

  // Load settings from localStorage on mount
  useEffect(() => {
    const saved = localStorage.getItem("chat-settings");
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        setSettings({ ...DEFAULT_SETTINGS, ...parsed });
      } catch (error) {
        console.error("Failed to load settings:", error);
      }
    }
  }, []);

  // Save settings to localStorage when changed
  useEffect(() => {
    localStorage.setItem("chat-settings", JSON.stringify(settings));
    // TODO: Sync with backend API
  }, [settings]);

  const updateSetting = <K extends keyof SettingsState>(
    key: K,
    value: SettingsState[K]
  ) => {
    setSettings((prev) => ({ ...prev, [key]: value }));
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button variant="ghost" size="icon">
          <Settings className="h-4 w-4" />
          <span className="sr-only">Open settings</span>
        </Button>
      </DialogTrigger>
      <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Chat Settings</DialogTitle>
          <DialogDescription>
            Configure display preferences and behavior options.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6 py-4">
          {/* Metadata Display Section */}
          <div className="space-y-4">
            <h3 className="text-sm font-semibold">Metadata Display</h3>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <Label htmlFor="show-metadata" className="text-sm">
                  Show Metadata Panel
                </Label>
                <Switch
                  id="show-metadata"
                  checked={settings.showMetadata}
                  onCheckedChange={(checked) =>
                    updateSetting("showMetadata", checked)
                  }
                />
              </div>
              <div className="flex items-center justify-between">
                <Label htmlFor="show-sql" className="text-sm">
                  Show SQL Queries
                </Label>
                <Switch
                  id="show-sql"
                  checked={settings.showSql}
                  onCheckedChange={(checked) => updateSetting("showSql", checked)}
                />
              </div>
              <div className="flex items-center justify-between">
                <Label htmlFor="show-chunks" className="text-sm">
                  Show Chunks
                </Label>
                <Switch
                  id="show-chunks"
                  checked={settings.showChunks}
                  onCheckedChange={(checked) =>
                    updateSetting("showChunks", checked)
                  }
                />
              </div>
              <div className="flex items-center justify-between">
                <Label htmlFor="show-scores" className="text-sm">
                  Show Similarity Scores
                </Label>
                <Switch
                  id="show-scores"
                  checked={settings.showScores}
                  onCheckedChange={(checked) =>
                    updateSetting("showScores", checked)
                  }
                />
              </div>
              <div className="flex items-center justify-between">
                <Label htmlFor="show-metrics" className="text-sm">
                  Show Performance Metrics
                </Label>
                <Switch
                  id="show-metrics"
                  checked={settings.showMetrics}
                  onCheckedChange={(checked) =>
                    updateSetting("showMetrics", checked)
                  }
                />
              </div>
              <div className="flex items-center justify-between">
                <Label htmlFor="highlight-citations" className="text-sm">
                  Highlight Citations
                </Label>
                <Switch
                  id="highlight-citations"
                  checked={settings.highlightCitations}
                  onCheckedChange={(checked) =>
                    updateSetting("highlightCitations", checked)
                  }
                />
              </div>
            </div>
          </div>

          <Separator />

          {/* Formatting Section */}
          <div className="space-y-4">
            <h3 className="text-sm font-semibold">Formatting</h3>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <Label htmlFor="format-code" className="text-sm">
                  Format Code Blocks
                </Label>
                <Switch
                  id="format-code"
                  checked={settings.formatCode}
                  onCheckedChange={(checked) =>
                    updateSetting("formatCode", checked)
                  }
                />
              </div>
              <div className="flex items-center justify-between">
                <Label htmlFor="syntax-highlighting" className="text-sm">
                  Syntax Highlighting
                </Label>
                <Switch
                  id="syntax-highlighting"
                  checked={settings.syntaxHighlighting}
                  onCheckedChange={(checked) =>
                    updateSetting("syntaxHighlighting", checked)
                  }
                />
              </div>
              <div className="flex items-center justify-between">
                <Label htmlFor="format-numbers" className="text-sm">
                  Format Numbers
                </Label>
                <Switch
                  id="format-numbers"
                  checked={settings.formatNumbers}
                  onCheckedChange={(checked) =>
                    updateSetting("formatNumbers", checked)
                  }
                />
              </div>
              <div className="flex items-center justify-between">
                <Label htmlFor="format-dates" className="text-sm">
                  Format Dates
                </Label>
                <Switch
                  id="format-dates"
                  checked={settings.formatDates}
                  onCheckedChange={(checked) =>
                    updateSetting("formatDates", checked)
                  }
                />
              </div>
            </div>
          </div>

          <Separator />

          {/* Behavior Section */}
          <div className="space-y-4">
            <h3 className="text-sm font-semibold">Behavior</h3>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <Label htmlFor="auto-scroll" className="text-sm">
                  Auto-scroll to Latest
                </Label>
                <Switch
                  id="auto-scroll"
                  checked={settings.autoScroll}
                  onCheckedChange={(checked) =>
                    updateSetting("autoScroll", checked)
                  }
                />
              </div>
              <div className="flex items-center justify-between">
                <Label htmlFor="notifications" className="text-sm">
                  Enable Notifications
                </Label>
                <Switch
                  id="notifications"
                  checked={settings.notifications}
                  onCheckedChange={(checked) =>
                    updateSetting("notifications", checked)
                  }
                />
              </div>
              <div className="flex items-center justify-between">
                <Label htmlFor="confirmations" className="text-sm">
                  Show Confirmations
                </Label>
                <Switch
                  id="confirmations"
                  checked={settings.confirmations}
                  onCheckedChange={(checked) =>
                    updateSetting("confirmations", checked)
                  }
                />
              </div>
            </div>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}

