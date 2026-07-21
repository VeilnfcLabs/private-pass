"use client";

import { create } from "zustand";

interface QRState {
  url: string;
  format: "png" | "svg";
  errorCorrection: "L" | "M" | "Q" | "H";
  size: number;
  margin: number;
  color: string;
  bgColor: string;
  expirationEnabled: boolean;
  expirationDuration: number;
  oneTimeUse: boolean;
  includeSignature: boolean;
  generatedData: string | null;
  isGenerating: boolean;
  error: string | null;
  setUrl: (url: string) => void;
  setFormat: (format: "png" | "svg") => void;
  setErrorCorrection: (level: "L" | "M" | "Q" | "H") => void;
  setSize: (size: number) => void;
  setMargin: (margin: number) => void;
  setColor: (color: string) => void;
  setBgColor: (color: string) => void;
  setExpirationEnabled: (enabled: boolean) => void;
  setExpirationDuration: (duration: number) => void;
  setOneTimeUse: (oneTime: boolean) => void;
  setIncludeSignature: (include: boolean) => void;
  setGeneratedData: (data: string | null) => void;
  setError: (error: string | null) => void;
  reset: () => void;
}

const initialState = {
  url: "",
  format: "png" as const,
  errorCorrection: "M" as const,
  size: 256,
  margin: 2,
  color: "#6366f1",
  bgColor: "#ffffff",
  expirationEnabled: false,
  expirationDuration: 24,
  oneTimeUse: false,
  includeSignature: false,
  generatedData: null as string | null,
  isGenerating: false,
  error: null as string | null,
};

export const useQRStore = create<QRState>()((set) => ({
  ...initialState,
  setUrl: (url) => set({ url }),
  setFormat: (format) => set({ format }),
  setErrorCorrection: (errorCorrection) => set({ errorCorrection }),
  setSize: (size) => set({ size }),
  setMargin: (margin) => set({ margin }),
  setColor: (color) => set({ color }),
  setBgColor: (bgColor) => set({ bgColor }),
  setExpirationEnabled: (expirationEnabled) => set({ expirationEnabled }),
  setExpirationDuration: (expirationDuration) => set({ expirationDuration }),
  setOneTimeUse: (oneTimeUse) => set({ oneTimeUse }),
  setIncludeSignature: (includeSignature) => set({ includeSignature }),
  setGeneratedData: (generatedData) => set({ generatedData }),
  setError: (error) => set({ error }),
  reset: () => set(initialState),
}));
