"use client";

import React from "react";
import { useThemeStore } from "@/lib/stores/themeStore";
import { Button } from "@/components/ui/button";
import { Sun, Moon, Github, Menu } from "lucide-react";

interface NavbarProps {
  onMenuClick: () => void;
}

export function Navbar({ onMenuClick }: NavbarProps) {
  const { theme, toggleTheme } = useThemeStore();

  return (
    <header className="sticky top-0 z-30 bg-surface/80 backdrop-blur-lg border-b border-border">
      <div className="flex items-center justify-between px-4 lg:px-6 h-16">
        <div className="flex items-center gap-3">
          <button
            onClick={onMenuClick}
            className="lg:hidden p-2 rounded-lg text-text-secondary hover:bg-surface-elevated transition-colors"
          >
            <Menu size={20} />
          </button>
          <div className="hidden lg:flex items-center gap-2">
            <h1 className="text-lg font-semibold text-text-primary">VeilPass</h1>
            <span className="text-xs text-text-muted bg-surface-elevated px-2 py-0.5 rounded-full">
              v0.1.0
            </span>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={toggleTheme}
            className="p-2 rounded-lg text-text-secondary hover:bg-surface-elevated hover:text-text-primary transition-all duration-200"
            aria-label="Toggle theme"
          >
            {theme === "dark" ? <Sun size={18} /> : <Moon size={18} />}
          </button>
          <a
            href="https://github.com/veillabs/veilpass"
            target="_blank"
            rel="noopener noreferrer"
            className="p-2 rounded-lg text-text-secondary hover:bg-surface-elevated hover:text-text-primary transition-all duration-200"
            aria-label="GitHub"
          >
            <Github size={18} />
          </a>
        </div>
      </header>
    );
  }
}
