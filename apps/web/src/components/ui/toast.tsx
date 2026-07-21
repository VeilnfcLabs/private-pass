"use client";

import React, { useEffect, useState } from "react";
import { cn } from "@/lib/utils";
import { X, CheckCircle, AlertCircle, AlertTriangle, Info } from "lucide-react";

type ToastType = "success" | "error" | "warning" | "info";

interface Toast {
  id: string;
  message: string;
  type: ToastType;
}

type ToastListener = (toast: Toast) => void;

let toastListeners: ToastListener[] = [];
let toastId = 0;

export function showToast(message: string, type: ToastType = "info") {
  const toast: Toast = { id: String(++toastId), message, type };
  toastListeners.forEach((fn) => fn(toast));
}

export function ToastContainer() {
  const [toasts, setToasts] = useState<Toast[]>([]);

  useEffect(() => {
    const listener: ToastListener = (toast) => {
      setToasts((prev) => [...prev, toast]);
      setTimeout(() => {
        setToasts((prev) => prev.filter((t) => t.id !== toast.id));
      }, 4000);
    };
    toastListeners.push(listener);
    return () => {
      toastListeners = toastListeners.filter((l) => l !== listener);
    };
  }, []);

  if (toasts.length === 0) return null;

  return (
    <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2 max-w-sm">
      {toasts.map((toast) => (
        <div
          key={toast.id}
          className={cn(
            "glass-card px-4 py-3 flex items-center gap-3 animate-slide-in shadow-lg",
            toast.type === "success" && "border-emerald-500/30",
            toast.type === "error" && "border-red-500/30",
            toast.type === "warning" && "border-amber-500/30",
            toast.type === "info" && "border-blue-500/30"
          )}
        >
          {toast.type === "success" && <CheckCircle size={16} className="text-emerald-400" />}
          {toast.type === "error" && <AlertCircle size={16} className="text-red-400" />}
          {toast.type === "warning" && <AlertTriangle size={16} className="text-amber-400" />}
          {toast.type === "info" && <Info size={16} className="text-blue-400" />}
          <p className="text-sm text-text-primary flex-1">{toast.message}</p>
          <button
            onClick={() => {
              setToasts((prev) => prev.filter((t) => t.id !== toast.id));
            }}
            className="text-text-muted hover:text-text-primary"
          >
            <X size={14} />
          </button>
        </div>
      ))}
    </div>
  );
}
