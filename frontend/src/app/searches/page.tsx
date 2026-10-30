"use client";

import { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { getSearches, deleteSearch, updateSearch } from "@/lib/api";
import SearchForm from "@/components/SearchForm";
import DealBadge from "@/components/DealBadge";

interface Search {
  id: string;
  name: string;
  make: string;
  model?: string;
  is_active: boolean;
  last_scan_at?: string;
  listing_count?: number;
  top_deal_score?: number;
}

export default function SearchesPage() {
  const [searches, setSearches] = useState<Search[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editData, setEditData] = useState<any>(null);

  const loadSearches = useCallback(async () => {
    try {
      const data = await getSearches();
      setSearches(Array.isArray(data) ? data : []);
    } catch {
      // API not available
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadSearches();
  }, [loadSearches]);

  const handleToggle = async (search: Search) => {
    try {
      await updateSearch(search.id, { is_active: !search.is_active });
      loadSearches();
    } catch {
      // error
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Weet je zeker dat je deze zoekopdracht wilt verwijderen?")) return;
    try {
      await deleteSearch(id);
      loadSearches();
    } catch {
      // error
    }
  };

  const handleEdit = (search: Search) => {
    setEditData(search);
    setShowForm(true);
  };

  const handleFormClose = () => {
    setShowForm(false);
    setEditData(null);
  };

  const handleFormSaved = () => {
    setShowForm(false);
    setEditData(null);
    loadSearches();
  };

  const formatDate = (dateStr?: string) => {
    if (!dateStr) return "Nog niet gescand";
    const d = new Date(dateStr);
    return d.toLocaleString("nl-NL", {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  if (loading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-blue-500 border-t-transparent" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Zoekopdrachten</h1>
          <p className="text-sm text-slate-400">Beheer je auto zoekopdrachten</p>
        </div>
        <button
          onClick={() => setShowForm(true)}
          className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-500"
        >
          Nieuwe zoekopdracht
        </button>
      </div>

      {searches.length === 0 ? (
        <div className="rounded-xl bg-slate-800 p-8 text-center">
          <svg className="mx-auto mb-4 h-12 w-12 text-slate-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z" />
          </svg>
          <p className="text-slate-400">Nog geen zoekopdrachten. Maak je eerste aan!</p>
        </div>
      ) : (
        <div className="space-y-3">
          {searches.map((search) => (
            <div
              key={search.id}
              className="flex flex-col gap-3 rounded-xl bg-slate-800 p-4 sm:flex-row sm:items-center sm:justify-between"
            >
              <Link href={`/searches/${search.id}`} className="flex-1 min-w-0">
                <h3 className="font-semibold text-white truncate">{search.name}</h3>
                <p className="text-sm text-slate-400">
                  {search.make}
                  {search.model ? ` ${search.model}` : ""}
                </p>
                <div className="mt-1 flex flex-wrap items-center gap-3 text-xs text-slate-500">
                  <span>Laatste scan: {formatDate(search.last_scan_at)}</span>
                  {search.listing_count !== undefined && (
                    <span>{search.listing_count} resultaten</span>
                  )}
                </div>
              </Link>

              <div className="flex items-center gap-3">
                {search.top_deal_score !== undefined && (
                  <DealBadge score={search.top_deal_score} size="sm" />
                )}

                {/* Toggle */}
                <button
                  onClick={() => handleToggle(search)}
                  className={`relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full transition-colors ${
                    search.is_active ? "bg-blue-600" : "bg-slate-600"
                  }`}
                >
                  <span
                    className={`inline-block h-5 w-5 transform rounded-full bg-white shadow transition-transform ${
                      search.is_active ? "translate-x-5" : "translate-x-0.5"
                    } mt-0.5`}
                  />
                </button>

                {/* Edit */}
                <button
                  onClick={() => handleEdit(search)}
                  className="rounded-lg p-2 text-slate-400 hover:bg-slate-700 hover:text-white"
                  title="Bewerken"
                >
                  <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L10.582 16.07a4.5 4.5 0 01-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 011.13-1.897l8.932-8.931zm0 0L19.5 7.125M18 14v4.75A2.25 2.25 0 0115.75 21H5.25A2.25 2.25 0 013 18.75V8.25A2.25 2.25 0 015.25 6H10" />
                  </svg>
                </button>

                {/* Delete */}
                <button
                  onClick={() => handleDelete(search.id)}
                  className="rounded-lg p-2 text-slate-400 hover:bg-red-900/50 hover:text-red-400"
                  title="Verwijderen"
                >
                  <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0" />
                  </svg>
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {showForm && (
        <SearchForm
          initialData={editData}
          onClose={handleFormClose}
          onSaved={handleFormSaved}
        />
      )}
    </div>
  );
}
