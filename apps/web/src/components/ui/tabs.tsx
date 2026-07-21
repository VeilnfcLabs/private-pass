"use client";

import React, { useState } from "react";
import { cn } from "@/lib/utils";

interface TabsProps {
  tabs: { id: string; label: string; content: React.ReactNode }[];
  defaultTab?: string;
  className?: string;
}

export function Tabs({ tabs, defaultTab, className }: TabsProps) {
  const [activeTab, setActiveTab] = useState(defaultTab || tabs[0]?.id || "");

  return (
    <div className={cn("flex flex-col", className)}>
      <div className="flex border-b border-border overflow-x-auto">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={cn(
              "px-4 py-2.5 text-sm font-medium transition-all duration-200 border-b-2 -mb-px whitespace-nowrap",
              activeTab === tab.id
                ? "border-primary-500 text-primary-400"
                : "border-transparent text-text-muted hover:text-text-secondary"
            )}
          >
            {tab.label}
          </button>
        ))}
      </div>
      <div className="mt-4 animate-fade-in">
        {tabs.find((t) => t.id === activeTab)?.content}
      </div>
    </div>
  );
}
