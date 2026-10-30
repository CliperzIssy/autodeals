"use client";

interface DealBadgeProps {
  score: number | null | undefined;
  size?: "sm" | "md" | "lg";
}

export default function DealBadge({ score, size = "md" }: DealBadgeProps) {
  if (score === null || score === undefined) {
    return (
      <span className="badge-deal-neutral">
        -
      </span>
    );
  }

  let className: string;
  let label: string;

  if (score >= 70) {
    className = "badge-deal-good";
    label = "Top deal";
  } else if (score >= 50) {
    className = "badge-deal-warning";
    label = "Redelijk";
  } else {
    className = "badge-deal-bad";
    label = "Matig";
  }

  const sizeClasses = {
    sm: "text-xs px-1.5 py-0.5",
    md: "text-sm px-2 py-0.5",
    lg: "text-base px-3 py-1",
  };

  return (
    <span className={`${className} ${sizeClasses[size]} inline-flex items-center gap-1 rounded-full font-semibold`}>
      <span>{score}</span>
      {size !== "sm" && <span className="opacity-80">· {label}</span>}
    </span>
  );
}
