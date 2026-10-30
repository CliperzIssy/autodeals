"use client";

import { useState, useEffect } from "react";

export default function SettingsPage() {
  const [user, setUser] = useState<{ name?: string; email?: string; company_name?: string } | null>(null);

  useEffect(() => {
    // Try to decode user info from JWT token (simplified)
    try {
      const token = localStorage.getItem("autodeals_token");
      if (token) {
        const payload = JSON.parse(atob(token.split(".")[1]));
        setUser({
          name: payload.name || payload.sub,
          email: payload.email || payload.sub,
          company_name: payload.company_name,
        });
      }
    } catch {
      // Unable to decode token
    }
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Instellingen</h1>
        <p className="text-sm text-slate-400">Account en app instellingen</p>
      </div>

      {/* Account Info */}
      <div className="rounded-xl bg-slate-800 p-5">
        <h2 className="mb-4 text-sm font-semibold text-slate-300">Account informatie</h2>
        <div className="space-y-3">
          <div>
            <p className="text-xs text-slate-500">Naam</p>
            <p className="text-sm font-medium">{user?.name || "-"}</p>
          </div>
          <div>
            <p className="text-xs text-slate-500">E-mail</p>
            <p className="text-sm font-medium">{user?.email || "-"}</p>
          </div>
          {user?.company_name && (
            <div>
              <p className="text-xs text-slate-500">Bedrijf</p>
              <p className="text-sm font-medium">{user.company_name}</p>
            </div>
          )}
        </div>
      </div>

      {/* Notifications placeholder */}
      <div className="rounded-xl bg-slate-800 p-5">
        <h2 className="mb-4 text-sm font-semibold text-slate-300">Meldingen</h2>
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium">E-mail meldingen</p>
              <p className="text-xs text-slate-500">Ontvang meldingen bij nieuwe top deals</p>
            </div>
            <div className="relative inline-flex h-6 w-11 cursor-pointer rounded-full bg-slate-600 transition-colors">
              <span className="mt-0.5 ml-0.5 inline-block h-5 w-5 rounded-full bg-white shadow transition-transform" />
            </div>
          </div>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium">Dagelijkse samenvatting</p>
              <p className="text-xs text-slate-500">Dagelijkse e-mail met nieuwe resultaten</p>
            </div>
            <div className="relative inline-flex h-6 w-11 cursor-pointer rounded-full bg-slate-600 transition-colors">
              <span className="mt-0.5 ml-0.5 inline-block h-5 w-5 rounded-full bg-white shadow transition-transform" />
            </div>
          </div>
        </div>
      </div>

      {/* Scan Settings placeholder */}
      <div className="rounded-xl bg-slate-800 p-5">
        <h2 className="mb-4 text-sm font-semibold text-slate-300">Scan instellingen</h2>
        <div className="space-y-3">
          <div>
            <p className="text-sm font-medium text-slate-400">Scan interval</p>
            <p className="text-xs text-slate-500">Hoe vaak worden zoekopdrachten automatisch gescand</p>
            <select className="mt-1 rounded-lg border border-slate-600 bg-slate-700 px-3 py-1.5 text-sm text-white focus:border-blue-500 focus:outline-none">
              <option>Elk uur</option>
              <option>Elke 4 uur</option>
              <option>Elke 12 uur</option>
              <option>Dagelijks</option>
            </select>
          </div>
        </div>
      </div>
    </div>
  );
}
