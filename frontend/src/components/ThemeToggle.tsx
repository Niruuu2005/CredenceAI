import { useEffect, useState, useRef } from "react";
import { Palette, Check, Sun, Moon } from "lucide-react";
import { cn } from "@/lib/utils";

type ThemeOption = {
  id: string;
  name: string;
  className: string;
  isDark: boolean;
};

const THEMES: ThemeOption[] = [
  { id: "classic-light", name: "Classic Light", className: "", isDark: false },
  { id: "classic-dark", name: "Classic Dark", className: "dark", isDark: true },
  { id: "forest-light", name: "Forest Light", className: "theme-forest-light", isDark: false },
  { id: "forest-dark", name: "Forest Dark", className: "theme-forest-dark dark", isDark: true },
  { id: "clay-light", name: "Clay Light", className: "theme-clay-light", isDark: false },
  { id: "clay-dark", name: "Clay Dark", className: "theme-clay-dark dark", isDark: true },
  { id: "slate-light", name: "Slate Light", className: "theme-slate-light", isDark: false },
  { id: "slate-dark", name: "Slate Dark", className: "theme-slate-dark dark", isDark: true },
];

export function ThemeToggle() {
  const [activeThemeId, setActiveThemeId] = useState(() => {
    return localStorage.getItem("workspace_theme") || "classic-light";
  });
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleOutsideClick = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener("mousedown", handleOutsideClick);
    return () => document.removeEventListener("mousedown", handleOutsideClick);
  }, []);

  useEffect(() => {
    const root = window.document.documentElement;
    
    // Remove all possible theme classes
    root.classList.remove("dark");
    THEMES.forEach((t) => {
      if (t.className) {
        t.className.split(" ").forEach((c) => root.classList.remove(c));
      }
    });

    // Add current theme class(es)
    const activeTheme = THEMES.find((t) => t.id === activeThemeId) || THEMES[0];
    if (activeTheme.className) {
      activeTheme.className.split(" ").forEach((c) => root.classList.add(c));
    }
    
    localStorage.setItem("workspace_theme", activeThemeId);
  }, [activeThemeId]);

  const activeTheme = THEMES.find((t) => t.id === activeThemeId) || THEMES[0];

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="h-10 px-3.5 rounded-xl bg-bg-deep border-none text-text-body flex items-center justify-center gap-2.5 cursor-pointer neu-outset-sm active:scale-95 transition-all select-none focus:outline-none"
        aria-label="Select Theme"
        id="theme-select-btn"
      >
        <Palette className="h-4 w-4 text-primary" />
        <span className="text-[10px] uppercase tracking-wider font-extrabold hidden sm:inline">
          {activeTheme.name}
        </span>
        {activeTheme.isDark ? <Moon className="h-3.5 w-3.5 text-primary" /> : <Sun className="h-3.5 w-3.5 text-amber-500" />}
      </button>

      {isOpen && (
        <div className="absolute right-0 mt-3 w-56 bg-bg-deep rounded-2xl p-2.5 neu-outset border-none z-50 animate-fade-in space-y-1">
          <div className="text-[9px] uppercase tracking-widest font-extrabold text-text-subtle px-2.5 py-2 border-b border-border-subtle/10 mb-1.5 select-none">
            Select Color Palette
          </div>
          <div className="max-h-64 overflow-y-auto pr-1 space-y-1">
            {THEMES.map((themeOption) => (
              <button
                key={themeOption.id}
                onClick={() => {
                  setActiveThemeId(themeOption.id);
                  setIsOpen(false);
                }}
                className={cn(
                  "w-full flex items-center justify-between px-3 py-2 rounded-xl text-left text-xs font-semibold transition-all hover:bg-bg-panel/40 cursor-pointer border-none",
                  activeThemeId === themeOption.id ? "text-primary bg-bg-panel font-bold neu-inset-sm" : "text-text-body"
                )}
              >
                <div className="flex items-center gap-2">
                  <span className={cn(
                    "w-2.5 h-2.5 rounded-full border border-border-subtle/10",
                    themeOption.isDark ? "bg-stone-700" : "bg-orange-100"
                  )} />
                  <span>{themeOption.name}</span>
                </div>
                {activeThemeId === themeOption.id && <Check className="h-3.5 w-3.5 text-primary" />}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
