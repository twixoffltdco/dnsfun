"use client";

import { CopyButton } from "./CopyButton";
import { cn } from "@/lib/utils";

interface DnsCardProps {
  title: string;
  description?: string;
  value: string;
  secondaryValue?: string;
  icon?: React.ReactNode;
  className?: string;
}

export function DnsCard({
  title,
  description,
  value,
  secondaryValue,
  icon,
  className,
}: DnsCardProps) {
  return (
    <div
      className={cn(
        "glass rounded-2xl p-6 transition-all hover:border-neon-cyan/30 hover:shadow-[0_0_30px_rgba(0,242,234,0.1)]",
        className
      )}
    >
      <div className="mb-4 flex items-center gap-3">
        {icon && (
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-neon-cyan/10 text-neon-cyan">
            {icon}
          </div>
        )}
        <div>
          <h3 className="text-lg font-semibold text-white">{title}</h3>
          {description && (
            <p className="text-sm text-white/50">{description}</p>
          )}
        </div>
      </div>

      <div className="space-y-3">
        <div className="code-block rounded-xl px-4 py-3 text-sm text-neon-cyan break-all">
          {value}
        </div>
        {secondaryValue && (
          <div className="code-block rounded-xl px-4 py-3 text-sm text-white/70 break-all">
            {secondaryValue}
          </div>
        )}
        <CopyButton text={value} />
      </div>
    </div>
  );
}
