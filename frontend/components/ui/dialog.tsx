"use client";

import { cn } from "@/lib/utils";
import { X } from "lucide-react";
import {
  createContext,
  useContext,
  useEffect,
  useRef,
  type ReactNode,
} from "react";

interface DialogContextValue {
  onClose: () => void;
}

const DialogContext = createContext<DialogContextValue>({
  onClose: () => {},
});

interface DialogProps {
  open: boolean;
  onClose: () => void;
  children: ReactNode;
}

export function Dialog({ open, onClose, children }: DialogProps) {
  const overlayRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, [open, onClose]);

  if (!open) return null;

  return (
    <DialogContext.Provider value={{ onClose }}>
      <div
        ref={overlayRef}
        className="fixed inset-0 z-50 flex items-center justify-center p-4"
        aria-modal="true"
        role="dialog"
      >
        {/* Backdrop */}
        <div
          className="absolute inset-0 bg-black/60 backdrop-blur-sm animate-fade-in"
          onClick={onClose}
        />
        {/* Panel */}
        <div className="relative z-10 w-full max-w-lg animate-slide-up">
          {children}
        </div>
      </div>
    </DialogContext.Provider>
  );
}

interface DialogPanelProps {
  children: ReactNode;
  className?: string;
}

export function DialogPanel({ children, className }: DialogPanelProps) {
  const { onClose } = useContext(DialogContext);

  return (
    <div
      className={cn(
        "rounded-lg border border-[hsl(var(--border))] bg-[hsl(var(--surface))]",
        "shadow-2xl shadow-black/50",
        className,
      )}
    >
      <button
        onClick={onClose}
        className="absolute right-4 top-4 text-[hsl(var(--muted-foreground))] hover:text-foreground transition-colors"
        aria-label="Close dialog"
      >
        <X size={16} />
      </button>
      {children}
    </div>
  );
}

export function DialogTitle({
  children,
  className,
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <h2
      className={cn(
        "text-base font-semibold text-foreground",
        className,
      )}
    >
      {children}
    </h2>
  );
}
