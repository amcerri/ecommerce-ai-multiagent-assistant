"use client";

import { useEffect } from "react";
import { Globe, Check } from "lucide-react";
import { useTranslation } from "react-i18next";

import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Badge } from "@/components/ui/badge";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { useLanguageStore } from "@/lib/store";

const languages = [
  { code: "pt-BR", name: "Português (Brasil)", native: "Português" },
  { code: "en-US", name: "English (US)", native: "English" },
  { code: "es-ES", name: "Español (España)", native: "Español" },
  { code: "fr-FR", name: "Français (France)", native: "Français" },
  { code: "de-DE", name: "Deutsch (Deutschland)", native: "Deutsch" },
];

export function LanguageSelector() {
  const { t } = useTranslation("common");
  const { language, autoDetect, setLanguage, setAutoDetect, loadLanguage } =
    useLanguageStore();

  useEffect(() => {
    // Load language preferences on mount
    loadLanguage();
  }, [loadLanguage]);

  const handleLanguageChange = (languageCode: string) => {
    setLanguage(languageCode);
  };

  const handleAutoDetectToggle = () => {
    setAutoDetect(!autoDetect);
  };

  const currentLang = languages.find((lang) => lang.code === language);

  return (
    <TooltipProvider>
      <DropdownMenu>
        <Tooltip>
          <TooltipTrigger asChild>
            <DropdownMenuTrigger asChild>
              <Button variant="outline" size="sm" className="gap-2">
                <Globe className="h-4 w-4" />
                <Badge variant="secondary" className="text-xs">
                  {currentLang?.code.toUpperCase()}
                </Badge>
              </Button>
            </DropdownMenuTrigger>
          </TooltipTrigger>
          <TooltipContent>
            <p>{t("nav.settings")}</p>
          </TooltipContent>
        </Tooltip>
        <DropdownMenuContent align="end" className="w-56">
          <DropdownMenuLabel>{t("nav.settings")}</DropdownMenuLabel>
          <DropdownMenuSeparator />
          {languages.map((lang) => (
            <DropdownMenuItem
              key={lang.code}
              onClick={() => handleLanguageChange(lang.code)}
              className="flex items-center justify-between"
            >
              <div className="flex flex-col">
                <span>{lang.native}</span>
                <span className="text-xs text-muted-foreground">
                  {lang.name}
                </span>
              </div>
              {language === lang.code && <Check className="h-4 w-4" />}
            </DropdownMenuItem>
          ))}
          <DropdownMenuSeparator />
          <DropdownMenuItem
            onClick={handleAutoDetectToggle}
            className="flex items-center justify-between"
          >
            <span>{t("language.autoDetect")}</span>
            {autoDetect && <Check className="h-4 w-4" />}
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    </TooltipProvider>
  );
}

