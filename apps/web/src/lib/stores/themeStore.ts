"use client";

import { create } from "zustand";

type Theme = "dark" | "light";

interface ThemeState {
  theme: Theme;
  hydrated: boolean;
  setTheme: (theme: Theme) => void;
  toggleTheme: () => void;
  hydrate: () => void;
}

function applyTheme(theme: Theme): void {
  if (typeof document === "undefined") return;
  document.documentElement.classList.toggle("light", theme === "light");
  document.documentElement.classList.toggle("dark", theme === "dark");
}

export const useThemeStore = create<ThemeState>()((set, get) => ({
  theme: "dark",
  hydrated: false,
  setTheme: (theme) => {
    set({ theme });
    localStorage.setItem("veilpass-theme", theme);
    applyTheme(theme);
  },
  toggleTheme: () => {
    const next = get().theme === "dark" ? "light" : "dark";
    get().setTheme(next);
  },
  hydrate: () => {
    if (typeof window === "undefined") return;
    const stored = localStorage.getItem("veilpass-theme");
    const theme: "dark" | "light" =
      stored === "light" || stored === "dark" ? stored : "dark";
    applyTheme(theme);
    set({ theme, hydrated: true });
  },
}));
