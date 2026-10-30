"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { getDashboardStats, getRecentDeals } from "@/lib/api";
import ListingCard from "@/components/ListingCard";

interface Stats {
  active_searches: number;
  new_listings_today: number;
  top_deals: number;
}

export default function DashboardPage() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [recentDeals, setRecentDeals] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const [statsData, dealsData] = await Promise.all([
          getDashboardStats(),
          getRecentDeals(),
        ]);
        setStats(statsData);
        setRecentDeals(dealsData.listings || dealsData || []);
      } catch {
        // API not available, show empty state
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  if (loading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-blue-500 border-t-transparent" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Dashboard</h1>
          <p className="text-sm text-slate-400">Overzicht van je auto zoekopdrachten</p>
        </div>
        <Link
          href="/searches"
          className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-500"
        >
          Nieuwe zoekopdracht
        </Link>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <div className="rounded-xl bg-slate-800 p-5">
          <p className="text-sm text-slate-400">Actieve zoekopdrachten</p>
          <p className="mt-1 text-3xl font-bold">{stats?.active_searches ?? 0}</p>
        </div>
        <div className="rounded-xl bg-slate-800 p-5">
          <p className="text-sm text-slate-400">Nieuwe aanbiedingen vandaag</p>
          <p className="mt-1 text-3xl font-bold">{stats?.new_listings_today ?? 0}</p>
        </div>
        <div className="rounded-xl bg-slate-800 p-5">
          <p className="text-sm text-slate-400">Top deals</p>
          <p className="mt-1 text-3xl font-bold text-green-400">{stats?.top_deals ?? 0}</p>
        </div>
      </div>

      {/* Recent Deals */}
      <div>
        <h2 className="mb-4 text-lg font-semibold">Recente top deals</h2>
        {recentDeals.length > 0 ? (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {recentDeals.map((listing: any) => (
              <ListingCard key={listing.id} listing={listing} />
            ))}
          </div>
        ) : (
          <div className="rounded-xl bg-slate-800 p-8 text-center">
            <p className="text-slate-400">
              Nog geen deals gevonden. Maak een zoekopdracht aan om te beginnen.
            </p>
            <Link
              href="/searches"
              className="mt-4 inline-block rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-500"
            >
              Eerste zoekopdracht aanmaken
            </Link>
          </div>
        )}
      </div>
    </div>
  );
}
