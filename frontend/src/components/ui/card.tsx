import { cn } from "../../lib/utils";

export function Card({ className = "", children }: { className?: string; children: any }) {
  return (
    <div className={cn("rounded-xl border bg-card text-card-foreground shadow-soft", className)}>
      {children}
    </div>
  );
}
