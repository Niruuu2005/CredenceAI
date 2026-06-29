import React, { useEffect, useState } from "react";
import { Sun, Moon } from "lucide-react";

export function ThemeToggle() {
  const [theme, setTheme] = useState<"light" | "dark">(() => {
    // Check local storage or default to light
    const stored = localStorage.getItem("theme");
    if (stored === "dark") return "dark";
    return "light";
  });

  useEffect(() => {
    const root = window.document.documentElement;
    if (theme === "dark") {
      root.classList.add("dark");
      localStorage.setItem("theme", "dark");
    } else {
      root.classList.remove("dark");
      localStorage.setItem("theme", "light");
    }
  }, [theme]);

  const toggleTheme = () => {
    setTheme((prev) => (prev === "light" ? "dark" : "light"));
  };

  return (
    <button
      onClick={toggleTheme}
      className="p-2 border border-border-subtle hover:border-border-accent transition-colors bg-bg-surface flex items-center justify-center cursor-pointer relative"
      aria-label="Toggle Theme"
      id="theme-toggle-btn"
    >
      {theme === "light" ? (
        <Moon className="h-4 w-4 text-text-title transition-all animate-fade-in" />
      ) : (
        <Sun className="h-4 w-4 text-text-title transition-all animate-fade-in" />
      )}
    </button>
  );
}
