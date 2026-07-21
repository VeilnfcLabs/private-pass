"use client";

import { create } from "zustand";

interface NFCState {
  issuer: string;
  payload: string;
  version: string;
  type: "uri" | "text" | "smart_poster" | "mime" | "external";
  expiration: string;
  metadata: string;
  generatedPayload: Record<string, unknown> | null;
  hex: string | null;
  base64: string | null;
  ndef: string | null;
  isGenerating: boolean;
  error: string | null;
  setIssuer: (issuer: string) => void;
  setPayload: (payload: string) => void;
  setVersion: (version: string) => void;
  setType: (type: "uri" | "text" | "smart_poster" | "mime" | "external") => void;
  setExpiration: (expiration: string) => void;
  setMetadata: (metadata: string) => void;
  setGeneratedPayload: (payload: Record<string, unknown> | null) => void;
  setHex: (hex: string | null) => void;
  setBase64: (base64: string | null) => void;
  setNdef: (ndef: string | null) => void;
  setError: (error: string | null) => void;
  reset: () => void;
}

const initialState: Omit<NFCState, "setIssuer" | "setPayload" | "setVersion" | "setType" | "setExpiration" | "setMetadata" | "setGeneratedPayload" | "setHex" | "setBase64" | "setNdef" | "setError" | "reset"> = {
  issuer: "",
  payload: "",
  version: "1.0",
  type: "uri",
  expiration: "",
  metadata: "{}",
  generatedPayload: null,
  hex: null,
  base64: null,
  ndef: null,
  isGenerating: false,
  error: null,
};

export const useNFCStore = create<NFCState>()((set) => ({
  ...initialState,
  setIssuer: (issuer) => set({ issuer }),
  setPayload: (payload) => set({ payload }),
  setVersion: (version) => set({ version }),
  setType: (type) => set({ type }),
  setExpiration: (expiration) => set({ expiration }),
  setMetadata: (metadata) => set({ metadata }),
  setGeneratedPayload: (generatedPayload) => set({ generatedPayload }),
  setHex: (hex) => set({ hex }),
  setBase64: (base64) => set({ base64 }),
  setNdef: (ndef) => set({ ndef }),
  setError: (error) => set({ error }),
  reset: () => set(initialState),
}));
