"use client";

import { useState, useEffect, useCallback } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { getSearch, getSearchListings, triggerScan } from "@/lib/api";
import ListingCard from "@/components/ListingCard";
import KmBucketView from "@/components/KmBucketView";
import type { KmBucket } from "@/components/KmBucketView";
import DealBadge from "@/components/DealBadge";

type SortOption = "score" | "price_asc" | "price_desc" | "km" | "newest";

const SORT_OPTIONS: { value: SortOption; label: string }[] = [
  { value: "score", label: "Deal score" },
  { value: "price_asc", label: "Prijs laag-hoog" },
  { value: "price_desc", label: "Prijs hoog-laag" },
  { value: "km", label: "Kilometerstand" },
  { value: "newest", label: "Nieuwste" },
];

function formatPrice(price: number): string {
  return (
    "\u20AC" +
    price.toLocaleString("de-DE", { minimumFractionDigits: 0, maximumFractionDigits: 0 })
  );
}

function formatKm(km: number): string {
  return km.toLocaleString("de-DE") + " km";
}

export default function SearchDetailPage() {
  const params = useParams();
  const searchId = params.id as string;

  const [search, setSearch] = useState<any>(null);
  const [listings, setListings] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [scanning, setScanning] = useState(false);
  const [scanMessage, setScanMessage] = useState<string | null>(null);

  // Filters
  const [sort, setSort] = useState<SortOption>("score");
  const [kmBucket, setKmBucket] = useState(0);
  const [minScore, setMinScore] = useState(0);
  const [viewMode, setViewMode] = useState<"grid" | "table">("grid");
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [kmCounts, setKmCounts] = useState<Record<string, number>>({});

  const loadListings = useCallback(async () => {
    const buckets = [
      { min: undefined, max: undefined },
      { min: 0, max: 50000 },
      { min: 50000, max: 100000 },
      { min: 100000, max: 150000 },
      { min: 150000, max: undefined },
    ];
    const bucket = buckets[kmBucket];

    try {
      const data = await getSearchListings(searchId, {
        sort,
        km_min: bucket.min,
        km_max: bucket.max,
        min_score: minScore > 0 ? minScore : undefined,
        page,
        per_page: 24,
      });
      setListings(Array.isArray(data.listings) ? data.listings : []);
      setTotalPages(data.total_pages || 1);
      if (data.km_counts) setKmCounts(data.km_counts);
    } catch {
      setListings([]);
    }
  }, [searchId, sort, kmBucket, minScore, page]);

  useEffect(() => {
    async function load() {
      try {
        const [searchData] = await Promise.all([getSearch(searchId)]);
        setSearch(searchData);
      } catch {
        // error
      }
      await loadListings();
      setLoading(false);
    }
    load();
  }, [searchId, loadListings]);

  useEffect(() => {
    if (!loading) loadListings();
  }, [sort, kmBucket, minScore, page, loadListings, loading]);

  const handleScan = async () => {
    setScanning(true);
    setScanMessage(null);
    try {
      await triggerScan(searchId);
      setScanMessage("Scan gestart. Resultaten worden bijgewerkt...");
      // Initial reload after enqueue
      setTimeout(() => {
        loadListings();
        setScanning(false);
      }, 2000);
    } catch (error: any) {
      if (error?.response?.status === 409) {
        setScanMessage(error?.response?.data?.detail || "Er draait al een scan voor deze zoekopdracht.");
      } else {
        setScanMessage("Scan starten mislukt. Probeer opnieuw.");
      }
      setScanning(false);
    }
  };

  if (loading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-blue-500 border-t-transparent" />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div className="flex items-center gap-2">
            <Link href="/searches" className="text-slate-400 hover:text-white">
              <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 19.5L8.25 12l7.5-7.5" />
              </svg>
            </Link>
            <h1 className="text-xl font-bold">{search?.name || "Zoekopdracht"}</h1>
          </div>
          <p className="mt-0.5 text-sm text-slate-400">
            {search?.make} {search?.model || ""} &middot; {listings.length} resultaten
          </p>
        </div>
        <button
          onClick={handleScan}
          disabled={scanning}
          className="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-500 disabled:opacity-50"
        >
          {scanning ? (
            <>
              <svg className="h-4 w-4 animate-spin" viewBox="0 0 24 24" fill="none">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              Scannen...
            </>
          ) : (
            <>
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182m0-4.991v4.99" />
              </svg>
              Scan nu
            </>
          )}
        </button>
      </div>

      {scanMessage && (
        <div className="rounded-lg border border-amber-500/30 bg-amber-500/10 px-3 py-2 text-sm text-amber-200">
          {scanMessage}
        </div>
      )}

      {/* KM Bucket Tabs */}
      <KmBucketView
        activeBucket={kmBucket}
        onSelect={(index) => {
          setKmBucket(index);
          setPage(1);
        }}
        counts={kmCounts}
      />

      {/* Filter Bar */}
      <div className="flex flex-wrap items-center gap-3 rounded-xl bg-slate-800 p-3">
        {/* Sort */}
        <select
          value={sort}
          onChange={(e) => { setSort(e.target.value as SortOption); setPage(1); }}
          className="rounded-lg border border-slate-600 bg-slate-700 px-3 py-1.5 text-sm text-white focus:border-blue-500 focus:outline-none"
        >
          {SORT_OPTIONS.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>

        {/* Min score slider */}
        <div className="flex items-center gap-2">
          <label className="text-xs text-slate-400">Min score:</label>
          <input
            type="range"
            min="0"
            max="100"
            value={minScore}
            onChange={(e) => { setMinScore(parseInt(e.target.value)); setPage(1); }}
            className="h-1.5 w-24 cursor-pointer appearance-none rounded-full bg-slate-600"
          />
          <span className="w-8 text-xs text-slate-300">{minScore}</span>
        </div>

        {/* Spacer */}
        <div className="flex-1" />

        {/* View mode toggle */}
        <div className="flex rounded-lg bg-slate-700 p-0.5">
          <button
            onClick={() => setViewMode("grid")}
            className={`rounded-md px-2.5 py-1 text-xs font-medium ${
              viewMode === "grid" ? "bg-slate-600 text-white" : "text-slate-400"
            }`}
          >
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 6A2.25 2.25 0 016 3.75h2.25A2.25 2.25 0 0110.5 6v2.25a2.25 2.25 0 01-2.25 2.25H6a2.25 2.25 0 01-2.25-2.25V6zM3.75 15.75A2.25 2.25 0 016 13.5h2.25a2.25 2.25 0 012.25 2.25V18a2.25 2.25 0 01-2.25 2.25H6A2.25 2.25 0 013.75 18v-2.25zM13.5 6a2.25 2.25 0 012.25-2.25H18A2.25 2.25 0 0120.25 6v2.25A2.25 2.25 0 0118 10.5h-2.25a2.25 2.25 0 01-2.25-2.25V6zM13.5 15.75a2.25 2.25 0 012.25-2.25H18a2.25 2.25 0 012.25 2.25V18A2.25 2.25 0 0118 20.25h-2.25A2.25 2.25 0 0113.5 18v-2.25z" />
            </svg>
          </button>
          <button
            onClick={() => setViewMode("table")}
            className={`rounded-md px-2.5 py-1 text-xs font-medium ${
              viewMode === "table" ? "bg-slate-600 text-white" : "text-slate-400"
            }`}
          >
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 5.25h16.5m-16.5 4.5h16.5m-16.5 4.5h16.5m-16.5 4.5h16.5" />
            </svg>
          </button>
        </div>
      </div>

      {/* Results */}
      {listings.length === 0 ? (
        <div className="rounded-xl bg-slate-800 p-8 text-center">
          <p className="text-slate-400">Geen resultaten gevonden met deze filters.</p>
        </div>
      ) : viewMode === "grid" ? (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {listings.map((listing: any) => (
            <ListingCard key={listing.id} listing={listing} />
          ))}
        </div>
      ) : (
        /* Table view */
        <div className="overflow-x-auto rounded-xl bg-slate-800">
          <table className="w-full text-left text-sm">
            <thead className="border-b border-slate-700 text-xs text-slate-400">
              <tr>
                <th className="px-4 py-3">Auto</th>
                <th className="px-4 py-3">Prijs</th>
                <th className="px-4 py-3">Markt</th>
                <th className="px-4 py-3">KM</th>
                <th className="px-4 py-3">Jaar</th>
                <th className="px-4 py-3">Score</th>
                <th className="px-4 py-3">Locatie</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-700/50">
              {listings.map((listing: any) => (
                <tr key={listing.id} className="hover:bg-slate-750">
                  <td className="px-4 py-3">
                    <Link
                      href={`/listings/${listing.id}`}
                      className="font-medium text-white hover:text-blue-400"
                    >
                      {listing.title}
                    </Link>
                  </td>
                  <td className="px-4 py-3 font-semibold text-white">
                    {formatPrice(listing.price)}
                  </td>
                  <td className="px-4 py-3">
                    {listing.price_diff !== null && listing.price_diff !== undefined ? (
                      <span
                        className={`text-xs font-medium ${
                          listing.price_diff < 0 ? "text-green-400" : listing.price_diff > 0 ? "text-red-400" : "text-slate-400"
                        }`}
                      >
                        {listing.price_diff < 0
                          ? `${formatPrice(Math.abs(listing.price_diff))} onder`
                          : listing.price_diff > 0
                          ? `${formatPrice(listing.price_diff)} boven`
                          : "Gemiddeld"}
                      </span>
                    ) : (
                      <span className="text-xs text-slate-500">-</span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-slate-300">
                    {listing.km !== undefined && listing.km !== null ? formatKm(listing.km) : "-"}
                  </td>
                  <td className="px-4 py-3 text-slate-300">{listing.year || "-"}</td>
                  <td className="px-4 py-3">
                    <DealBadge score={listing.deal_score} size="sm" />
                  </td>
                  <td className="px-4 py-3 text-slate-400">{listing.location || "-"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-2">
          <button
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page === 1}
            className="rounded-lg border border-slate-600 px-3 py-1.5 text-sm text-slate-300 hover:bg-slate-700 disabled:opacity-30"
          >
            Vorige
          </button>
          <span className="text-sm text-slate-400">
            Pagina {page} van {totalPages}
          </span>
          <button
            onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
            disabled={page === totalPages}
            className="rounded-lg border border-slate-600 px-3 py-1.5 text-sm text-slate-300 hover:bg-slate-700 disabled:opacity-30"
          >
            Volgende
          </button>
        </div>
      )}
    </div>
  );
}
