"use client";

import React, { useEffect } from "react";
import { useThemeStore } from "@/lib/stores/themeStore";

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const hydrate = useThemeStore((state) => (state as any).hydrate);

  useEffect(() => {
    hydrate();
  }, [hydrate]);

  return <>{children}</>;
}
