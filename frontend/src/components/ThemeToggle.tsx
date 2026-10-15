import { useEffect, useState, useRef } from "react";
import { Check, Sun, Moon, Sparkles } from "lucide-react";
import { cn } from "@/lib/utils";

export type ThemeId = "dark" | "light" | "beige";

type ThemeOption = {
  id: ThemeId;
  name: string;
  subtitle: string;
  className: string;
  isDark: boolean;
  accentColor: string;
  swatchBg: string;
  icon: typeof Moon;
};

const THEMES: ThemeOption[] = [
  {
    id: "dark",
    name: "Dark",
    subtitle: "Obsidian & Emerald",
    className: "dark",
    isDark: true,
    accentColor: "#10b981",
    swatchBg: "#080b11",
    icon: Moon,
  },
  {
    id: "light",
    name: "Light",
    subtitle: "Pristine Zinc & White",
    className: "light",
    isDark: false,
    accentColor: "#059669",
    swatchBg: "#f8fafc",
    icon: Sun,
  },
  {
    id: "beige",
    name: "Beige",
    subtitle: "Light Sand & Warm Brown",
    className: "beige",
    isDark: false,
    accentColor: "#8b5a2b",
    swatchBg: "#faf6ed",
    icon: Sparkles,
  },
];

function resolveInitialTheme(): ThemeId {
  const saved = localStorage.getItem("workspace_theme");
  if (saved === "light" || saved === "pristine-light" || saved === "nordic-light") {
    return "light";
  }
  if (saved === "beige" || saved === "editorial-paper") {
    return "beige";
  }
  if (saved === "dark" || saved === "perplexity-dark" || saved === "linear-indigo" || saved === "cyber-cyan" || saved === "monochrome-dark") {
    return "dark";
  }
  return "dark";
}

export function ThemeToggle() {
  const [activeThemeId, setActiveThemeId] = useState<ThemeId>(resolveInitialTheme);
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleOutsideClick = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        setIsOpen(false);
      }
    };
    document.addEventListener("mousedown", handleOutsideClick);
    document.addEventListener("keydown", handleKeyDown);
    return () => {
      document.removeEventListener("mousedown", handleOutsideClick);
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, []);

  useEffect(() => {
    const root = window.document.documentElement;

    // Remove old theme classes
    root.classList.remove(
      "dark",
      "light",
      "beige",
      "theme-linear-indigo",
      "theme-cyber-cyan",
      "theme-monochrome-dark",
      "theme-pristine-light",
      "theme-nordic-light"
    );

    // Add current theme class and data-theme
    root.classList.add(activeThemeId);
    root.setAttribute("data-theme", activeThemeId);

    localStorage.setItem("workspace_theme", activeThemeId);
  }, [activeThemeId]);

  const activeTheme = THEMES.find((t) => t.id === activeThemeId) || THEMES[0];
  const ActiveIcon = activeTheme.icon;

  return (
    <div className="relative z-50" ref={dropdownRef}>
      <button
        type="button"
        onClick={(e) => {
          e.stopPropagation();
          setIsOpen((prev) => !prev);
        }}
        className="h-9 px-3.5 rounded-xl border text-text-body flex items-center justify-center gap-2 cursor-pointer hover:border-border-accent/40 shadow-xs active:scale-95 transition-all select-none focus:outline-none"
        style={{
          backgroundColor: "var(--background-surface)",
          borderColor: "var(--border-subtle)",
        }}
        aria-label="Select Theme"
        id="theme-select-btn"
      >
        <span
          className="w-2.5 h-2.5 rounded-full shrink-0 shadow-xs"
          style={{ backgroundColor: activeTheme.accentColor }}
        />
        <span className="text-xs font-semibold text-text-title hidden sm:inline">
          {activeTheme.name}
        </span>
        <ActiveIcon
          className={cn(
            "h-3.5 w-3.5 shrink-0",
            activeThemeId === "dark" && "text-emerald-400",
            activeThemeId === "light" && "text-amber-500",
            activeThemeId === "beige" && "text-[#8b5a2b]"
          )}
        />
      </button>

      {isOpen && (
        <div
          className="absolute right-0 mt-2 w-64 rounded-2xl p-2 border shadow-2xl z-[100] animate-fade-in space-y-1"
          style={{
            backgroundColor: "var(--background-surface)",
            borderColor: "var(--border-subtle)",
            boxShadow: "0 14px 35px -5px rgba(0, 0, 0, 0.25), 0 0 0 1px var(--border-subtle)",
          }}
        >
          <div className="text-[10px] uppercase tracking-wider font-bold text-text-subtle px-3 py-1.5 border-b border-border-subtle/50 mb-1 select-none flex items-center justify-between">
            <span>Workspace Theme</span>
            <span className="text-[9px] font-mono font-bold text-primary px-1.5 py-0.5 rounded bg-primary/10">
              3 THEMES
            </span>
          </div>

          <div className="space-y-1">
            {THEMES.map((themeOption) => {
              const Icon = themeOption.icon;
              const isSelected = activeThemeId === themeOption.id;

              return (
                <button
                  key={themeOption.id}
                  id={`theme-option-${themeOption.id}`}
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation();
                    setActiveThemeId(themeOption.id);
                    setIsOpen(false);
                  }}
                  className={cn(
                    "w-full flex items-center justify-between px-3 py-2.5 rounded-xl text-left text-xs transition-all cursor-pointer border",
                    isSelected
                      ? "text-text-title border-border-accent/40 shadow-xs font-semibold"
                      : "text-text-body hover:bg-background-panel border-transparent"
                  )}
                  style={{
                    backgroundColor: isSelected ? "var(--background-panel)" : "transparent",
                  }}
                >
                  <div className="flex items-center gap-3">
                    <div
                      className="w-7 h-7 rounded-lg border border-border-subtle flex items-center justify-center shrink-0 shadow-xs"
                      style={{
                        backgroundColor: themeOption.swatchBg,
                        borderColor: isSelected ? themeOption.accentColor : "var(--border-subtle)",
                      }}
                    >
                      <Icon
                        className="h-3.5 w-3.5"
                        style={{ color: themeOption.accentColor }}
                      />
                    </div>
                    <div>
                      <div className="font-semibold text-text-title leading-tight">
                        {themeOption.name}
                      </div>
                      <div className="text-[11px] text-text-subtle mt-0.5 font-normal">
                        {themeOption.subtitle}
                      </div>
                    </div>
                  </div>

                  {isSelected && (
                    <Check
                      className="h-4 w-4 shrink-0"
                      style={{ color: themeOption.accentColor }}
                    />
                  )}
                </button>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
