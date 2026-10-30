"use client";

interface RedFlag {
  type: string;
  severity: "high" | "medium" | "low";
  description: string;
}

interface RedFlagBadgeProps {
  flags: RedFlag[];
  compact?: boolean;
}

export default function RedFlagBadge({ flags, compact = false }: RedFlagBadgeProps) {
  if (!flags || flags.length === 0) return null;

  if (compact) {
    return (
      <span className="inline-flex items-center gap-1 rounded-full bg-red-900/60 px-2 py-0.5 text-xs font-medium text-red-300">
        <svg className="h-3 w-3" fill="currentColor" viewBox="0 0 20 20">
          <path
            fillRule="evenodd"
            d="M8.485 2.495c.673-1.167 2.357-1.167 3.03 0l6.28 10.875c.673 1.167-.168 2.625-1.516 2.625H3.72c-1.347 0-2.189-1.458-1.515-2.625L8.485 2.495zM10 6a.75.75 0 01.75.75v3.5a.75.75 0 01-1.5 0v-3.5A.75.75 0 0110 6zm0 9a1 1 0 100-2 1 1 0 000 2z"
            clipRule="evenodd"
          />
        </svg>
        {flags.length}
      </span>
    );
  }

  const severityColors = {
    high: "bg-red-900/60 text-red-300 border-red-700",
    medium: "bg-yellow-900/60 text-yellow-300 border-yellow-700",
    low: "bg-slate-700 text-slate-300 border-slate-600",
  };

  return (
    <div className="space-y-2">
      {flags.map((flag, i) => (
        <div
          key={i}
          className={`flex items-start gap-2 rounded-lg border p-2 ${severityColors[flag.severity]}`}
        >
          <svg className="mt-0.5 h-4 w-4 shrink-0" fill="currentColor" viewBox="0 0 20 20">
            <path
              fillRule="evenodd"
              d="M8.485 2.495c.673-1.167 2.357-1.167 3.03 0l6.28 10.875c.673 1.167-.168 2.625-1.516 2.625H3.72c-1.347 0-2.189-1.458-1.515-2.625L8.485 2.495zM10 6a.75.75 0 01.75.75v3.5a.75.75 0 01-1.5 0v-3.5A.75.75 0 0110 6zm0 9a1 1 0 100-2 1 1 0 000 2z"
              clipRule="evenodd"
            />
          </svg>
          <div>
            <span className="text-xs font-semibold uppercase tracking-wide">
              {flag.type}
            </span>
            <p className="text-sm">{flag.description}</p>
          </div>
        </div>
      ))}
    </div>
  );
}
