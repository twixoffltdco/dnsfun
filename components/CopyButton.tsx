"use client";

import { useState } from "react";
import { Copy, Check } from "lucide-react";
import { cn } from "@/lib/utils";

interface CopyButtonProps {
  text: string;
  label?: string;
  className?: string;
}

export function CopyButton({ text, label, className }: CopyButtonProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // fallback
      const ta = document.createElement("textarea");
      ta.value = text;
      document.body.appendChild(ta);
      ta.select();
      document.execCommand("copy");
      document.body.removeChild(ta);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <button
      onClick={handleCopy}
      className={cn(
        "btn-neon inline-flex items-center gap-2 rounded-xl px-4 py-2.5 text-sm font-medium transition-all",
        "bg-neon-cyan/10 border border-neon-cyan/30 text-neon-cyan hover:bg-neon-cyan/20",
        className
      )}
    >
      {copied ? (
        <>
          <Check className="h-4 w-4" />
          <span>Скопировано</span>
        </>
      ) : (
        <>
          <Copy className="h-4 w-4" />
          <span>{label ?? "Копировать"}</span>
        </>
      )}
    </button>
  );
}
