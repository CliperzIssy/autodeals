"use client";

import Link from "next/link";
import Image from "next/image";
import DealBadge from "./DealBadge";
import RedFlagBadge from "./RedFlagBadge";

interface ListingCardProps {
  listing: {
    id: string;
    title: string;
    price: number;
    year?: number;
    km?: number;
    fuel_type?: string;
    transmission?: string;
    location?: string;
    thumbnail_url?: string;
    deal_score?: number | null;
    price_diff?: number | null;
    market_avg_price?: number | null;
    red_flags?: { type: string; severity: "high" | "medium" | "low"; description: string }[];
    source?: string;
  };
}

function formatPrice(price: number): string {
  return (
    "\u20AC" +
    price.toLocaleString("de-DE", {
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    })
  );
}

function formatKm(km: number): string {
  return km.toLocaleString("de-DE") + " km";
}

export default function ListingCard({ listing }: ListingCardProps) {
  const priceDiff = listing.price_diff;

  return (
    <Link
      href={`/listings/${listing.id}`}
      className="group block overflow-hidden rounded-xl bg-slate-800 transition-all hover:bg-slate-750 hover:ring-1 hover:ring-slate-600"
    >
      {/* Thumbnail */}
      <div className="relative aspect-[16/10] w-full overflow-hidden bg-slate-700">
        {listing.thumbnail_url ? (
          <Image
            src={listing.thumbnail_url}
            alt={listing.title}
            fill
            className="object-cover transition-transform group-hover:scale-105"
            sizes="(max-width: 640px) 100vw, (max-width: 1024px) 50vw, 33vw"
          />
        ) : (
          <div className="flex h-full items-center justify-center text-slate-500">
            <svg className="h-12 w-12" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1}
                d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
              />
            </svg>
          </div>
        )}

        {/* Deal score badge overlay */}
        <div className="absolute right-2 top-2">
          <DealBadge score={listing.deal_score ?? null} size="sm" />
        </div>

        {/* Source badge */}
        {listing.source && (
          <div className="absolute left-2 top-2 rounded bg-black/60 px-1.5 py-0.5 text-xs text-slate-300">
            {listing.source}
          </div>
        )}
      </div>

      {/* Content */}
      <div className="p-3">
        <h3 className="mb-1 truncate text-sm font-semibold text-slate-100">
          {listing.title}
        </h3>

        {/* Price row */}
        <div className="mb-2 flex items-baseline gap-2">
          <span className="text-lg font-bold text-white">
            {formatPrice(listing.price)}
          </span>
          {priceDiff !== null && priceDiff !== undefined && (
            <span
              className={`text-xs font-medium ${
                priceDiff < 0 ? "text-green-400" : priceDiff > 0 ? "text-red-400" : "text-slate-400"
              }`}
            >
              {priceDiff < 0
                ? `${formatPrice(Math.abs(priceDiff))} onder markt`
                : priceDiff > 0
                ? `${formatPrice(priceDiff)} boven markt`
                : "Marktprijs"}
            </span>
          )}
        </div>

        {/* Meta row */}
        <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-slate-400">
          {listing.year && <span>{listing.year}</span>}
          {listing.km !== undefined && listing.km !== null && (
            <span>{formatKm(listing.km)}</span>
          )}
          {listing.fuel_type && <span>{listing.fuel_type}</span>}
          {listing.transmission && <span>{listing.transmission}</span>}
        </div>

        {/* Bottom row */}
        <div className="mt-2 flex items-center justify-between">
          {listing.location && (
            <span className="text-xs text-slate-500">{listing.location}</span>
          )}
          {listing.red_flags && listing.red_flags.length > 0 && (
            <RedFlagBadge flags={listing.red_flags} compact />
          )}
        </div>
      </div>
    </Link>
  );
}

export { formatPrice, formatKm };
