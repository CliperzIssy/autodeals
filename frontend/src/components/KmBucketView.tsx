"use client";

interface KmBucket {
  label: string;
  min: number | null;
  max: number | null;
  count?: number;
}

const KM_BUCKETS: KmBucket[] = [
  { label: "Alle", min: null, max: null },
  { label: "0-50k", min: 0, max: 50000 },
  { label: "50-100k", min: 50000, max: 100000 },
  { label: "100-150k", min: 100000, max: 150000 },
  { label: "150k+", min: 150000, max: null },
];

interface KmBucketViewProps {
  activeBucket: number;
  onSelect: (index: number, bucket: KmBucket) => void;
  counts?: Record<string, number>;
}

export default function KmBucketView({
  activeBucket,
  onSelect,
  counts,
}: KmBucketViewProps) {
  return (
    <div className="flex gap-1 overflow-x-auto rounded-lg bg-slate-800/50 p-1">
      {KM_BUCKETS.map((bucket, index) => {
        const isActive = activeBucket === index;
        const count = counts?.[bucket.label];

        return (
          <button
            key={bucket.label}
            onClick={() => onSelect(index, bucket)}
            className={`flex items-center gap-1.5 whitespace-nowrap rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${
              isActive
                ? "bg-blue-600 text-white"
                : "text-slate-400 hover:bg-slate-700 hover:text-slate-200"
            }`}
          >
            {bucket.label}
            {count !== undefined && (
              <span
                className={`rounded-full px-1.5 py-0.5 text-xs ${
                  isActive
                    ? "bg-blue-500 text-white"
                    : "bg-slate-700 text-slate-400"
                }`}
              >
                {count}
              </span>
            )}
          </button>
        );
      })}
    </div>
  );
}

export { KM_BUCKETS };
export type { KmBucket };
