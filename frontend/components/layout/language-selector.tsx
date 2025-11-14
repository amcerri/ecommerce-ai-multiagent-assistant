"use client";

import { useState, useEffect } from "react";
import { Globe, Check } from "lucide-react";

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

const languages = [
  { code: "pt-BR", name: "Português (Brasil)", native: "Português" },
  { code: "en-US", name: "English (US)", native: "English" },
  { code: "es-ES", name: "Español (España)", native: "Español" },
  { code: "fr-FR", name: "Français (France)", native: "Français" },
  { code: "de-DE", name: "Deutsch (Deutschland)", native: "Deutsch" },
];

export function LanguageSelector() {
  const [currentLanguage, setCurrentLanguage] = useState("pt-BR");
  const [autoDetect, setAutoDetect] = useState(true);

  useEffect(() => {
    // Load saved preferences from localStorage
    const savedLanguage = localStorage.getItem("language");
    const savedAutoDetect = localStorage.getItem("autoDetect");

    if (savedLanguage) {
      setCurrentLanguage(savedLanguage);
    }
    if (savedAutoDetect !== null) {
      setAutoDetect(savedAutoDetect === "true");
    }
  }, []);

  const handleLanguageChange = (languageCode: string) => {
    setCurrentLanguage(languageCode);
    localStorage.setItem("language", languageCode);
    // TODO: Update i18n context when implemented
  };

  const handleAutoDetectToggle = () => {
    const newValue = !autoDetect;
    setAutoDetect(newValue);
    localStorage.setItem("autoDetect", String(newValue));
    // TODO: Update i18n context when implemented
  };

  const currentLang = languages.find((lang) => lang.code === currentLanguage);

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
            <p>Select language</p>
          </TooltipContent>
        </Tooltip>
        <DropdownMenuContent align="end" className="w-56">
          <DropdownMenuLabel>Language</DropdownMenuLabel>
          <DropdownMenuSeparator />
          {languages.map((language) => (
            <DropdownMenuItem
              key={language.code}
              onClick={() => handleLanguageChange(language.code)}
              className="flex items-center justify-between"
            >
              <div className="flex flex-col">
                <span>{language.native}</span>
                <span className="text-xs text-muted-foreground">
                  {language.name}
                </span>
              </div>
              {currentLanguage === language.code && (
                <Check className="h-4 w-4" />
              )}
            </DropdownMenuItem>
          ))}
          <DropdownMenuSeparator />
          <DropdownMenuItem
            onClick={handleAutoDetectToggle}
            className="flex items-center justify-between"
          >
            <span>Detect automatically</span>
            {autoDetect && <Check className="h-4 w-4" />}
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    </TooltipProvider>
  );
}

