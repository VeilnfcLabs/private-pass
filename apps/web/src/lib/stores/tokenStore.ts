"use client";

import { create } from "zustand";

interface TokenState {
  subject: string;
  audience: string;
  issuer: string;
  expirationPreset: "5min" | "10min" | "30min" | "1h" | "custom";
  customExpiration: string;
  customClaims: string;
  generatedToken: string | null;
  decodedHeader: Record<string, unknown> | null;
  decodedPayload: Record<string, unknown> | null;
  decodedSignature: string | null;
  isGenerating: boolean;
  error: string | null;
  setSubject: (subject: string) => void;
  setAudience: (audience: string) => void;
  setIssuer: (issuer: string) => void;
  setExpirationPreset: (preset: "5min" | "10min" | "30min" | "1h" | "custom") => void;
  setCustomExpiration: (expiration: string) => void;
  setCustomClaims: (claims: string) => void;
  setGeneratedToken: (token: string | null) => void;
  setDecodedHeader: (header: Record<string, unknown> | null) => void;
  setDecodedPayload: (payload: Record<string, unknown> | null) => void;
  setDecodedSignature: (signature: string | null) => void;
  setError: (error: string | null) => void;
  reset: () => void;
}

const initialState = {
  subject: "",
  audience: "",
  issuer: "VeilPass",
  expirationPreset: "1h" as const,
  customExpiration: "",
  customClaims: "{}",
  generatedToken: null as string | null,
  decodedHeader: null as Record<string, unknown> | null,
  decodedPayload: null as Record<string, unknown> | null,
  decodedSignature: null as string | null,
  isGenerating: false,
  error: null as string | null,
};

export const useTokenStore = create<TokenState>()((set) => ({
  ...initialState,
  setSubject: (subject) => set({ subject }),
  setAudience: (audience) => set({ audience }),
  setIssuer: (issuer) => set({ issuer }),
  setExpirationPreset: (expirationPreset) => set({ expirationPreset }),
  setCustomExpiration: (customExpiration) => set({ customExpiration }),
  setCustomClaims: (customClaims) => set({ customClaims }),
  setGeneratedToken: (generatedToken) => set({ generatedToken }),
  setDecodedHeader: (decodedHeader) => set({ decodedHeader }),
  setDecodedPayload: (decodedPayload) => set({ decodedPayload }),
  setDecodedSignature: (decodedSignature) => set({ decodedSignature }),
  setError: (error) => set({ error }),
  reset: () => set(initialState),
}));
