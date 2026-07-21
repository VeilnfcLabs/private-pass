"use client";

import { create } from "zustand";

export interface HistoryItem {
  id: string;
  type: "qr" | "nfc" | "signed-link" | "signed-url" | "token";
  label: string;
  timestamp: number;
  data: string;
}

interface HistoryState {
  items: HistoryItem[];
  addItem: (item: Omit<HistoryItem, "id" | "timestamp">) => void;
  removeItem: (id: string) => void;
  clearHistory: () => void;
}

const HISTORY_KEY = "veilpass-history";
const MAX_ITEMS = 50;

function loadHistory(): HistoryItem[] {
  if (typeof window === "undefined") return [];
  try {
    const stored = localStorage.getItem(HISTORY_KEY);
    return stored ? JSON.parse(stored) : [];
  } catch {
    return [];
  }
}

function saveHistory(items: HistoryItem[]): void {
  if (typeof window === "undefined") return;
  try {
    localStorage.setItem(HISTORY_KEY, JSON.stringify(items.slice(0, MAX_ITEMS)));
  } catch {
    // Storage full or unavailable
  }
}

export const useHistoryStore = create<HistoryState>()((set, get) => ({
  items: loadHistory(),
  addItem: (item) => {
    const newItem: HistoryItem = {
      ...item,
      id: Math.random().toString(36).substring(2, 15),
      timestamp: Date.now(),
    };
    const items = [newItem, ...get().items].slice(0, MAX_ITEMS);
    set({ items });
    saveHistory(items);
  },
  removeItem: (id) => {
    const items = get().items.filter((i) => i.id !== id);
    set({ items });
    saveHistory(items);
  },
  clearHistory: () => {
    set({ items: [] });
    saveHistory([]);
  },
}));
