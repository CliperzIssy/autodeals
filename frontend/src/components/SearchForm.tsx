"use client";

import { useState, useEffect } from "react";
import { createSearch, updateSearch } from "@/lib/api";

const MAKES_MODELS: Record<string, string[]> = {
  Volkswagen: ["Golf", "Polo", "Passat", "Tiguan", "T-Roc", "T-Cross", "Touran", "Touareg", "ID.3", "ID.4", "Arteon", "Up", "Caddy", "Transporter"],
  BMW: ["1 Serie", "2 Serie", "3 Serie", "4 Serie", "5 Serie", "7 Serie", "X1", "X2", "X3", "X4", "X5", "X6", "Z4", "iX", "i4"],
  "Mercedes-Benz": ["A-Klasse", "B-Klasse", "C-Klasse", "E-Klasse", "S-Klasse", "CLA", "CLS", "GLA", "GLB", "GLC", "GLE", "GLS", "EQA", "EQC", "Vito"],
  Audi: ["A1", "A3", "A4", "A5", "A6", "A7", "A8", "Q2", "Q3", "Q5", "Q7", "Q8", "e-tron", "TT", "RS3", "RS6"],
  Toyota: ["Yaris", "Corolla", "Camry", "RAV4", "C-HR", "Aygo", "Prius", "Land Cruiser", "Hilux", "Supra", "GR86"],
  Ford: ["Fiesta", "Focus", "Mondeo", "Puma", "Kuga", "Explorer", "Mustang", "Transit", "Ranger", "Galaxy", "S-MAX"],
  Opel: ["Corsa", "Astra", "Mokka", "Crossland", "Grandland", "Insignia", "Combo", "Vivaro", "Zafira"],
  Peugeot: ["108", "208", "308", "508", "2008", "3008", "5008", "Partner", "Rifter", "Expert"],
  Renault: ["Clio", "Megane", "Captur", "Kadjar", "Arkana", "Scenic", "Kangoo", "Trafic", "Zoe", "Twingo"],
  Volvo: ["XC40", "XC60", "XC90", "S60", "S90", "V40", "V60", "V90", "C40", "EX30"],
  Skoda: ["Fabia", "Octavia", "Superb", "Kamiq", "Karoq", "Kodiaq", "Scala", "Enyaq"],
  SEAT: ["Ibiza", "Leon", "Arona", "Ateca", "Tarraco"],
  Hyundai: ["i10", "i20", "i30", "Tucson", "Kona", "Santa Fe", "IONIQ 5", "IONIQ 6"],
  Kia: ["Picanto", "Rio", "Ceed", "Sportage", "Sorento", "Niro", "EV6", "Stonic"],
  Mazda: ["2", "3", "6", "CX-3", "CX-5", "CX-30", "MX-5", "CX-60"],
  Fiat: ["500", "Panda", "Tipo", "500X", "500L", "Ducato"],
  Citroën: ["C1", "C3", "C4", "C5 X", "Berlingo", "C3 Aircross", "C5 Aircross"],
  Nissan: ["Micra", "Juke", "Qashqai", "X-Trail", "Leaf", "Navara", "Ariya"],
  Honda: ["Jazz", "Civic", "CR-V", "HR-V", "e", "ZR-V"],
};

const FUEL_TYPES = ["Benzine", "Diesel", "Elektrisch", "Hybride", "Plug-in Hybride", "LPG"];
const TRANSMISSIONS = ["Handgeschakeld", "Automaat"];

interface SearchFormData {
  id?: string;
  name: string;
  make: string;
  model: string;
  variant: string;
  year_min: string;
  year_max: string;
  km_min: string;
  km_max: string;
  price_min: string;
  price_max: string;
  fuel_type: string;
  transmission: string;
}

interface SearchFormProps {
  initialData?: Partial<SearchFormData>;
  onClose: () => void;
  onSaved: () => void;
}

export default function SearchForm({ initialData, onClose, onSaved }: SearchFormProps) {
  const [form, setForm] = useState<SearchFormData>({
    name: "",
    make: "",
    model: "",
    variant: "",
    year_min: "",
    year_max: "",
    km_min: "",
    km_max: "",
    price_min: "",
    price_max: "",
    fuel_type: "",
    transmission: "",
    ...initialData,
  });

  const [models, setModels] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (form.make && MAKES_MODELS[form.make]) {
      setModels(MAKES_MODELS[form.make]);
    } else {
      setModels([]);
    }
  }, [form.make]);

  const handleChange = (field: keyof SearchFormData, value: string) => {
    setForm((prev) => {
      const next = { ...prev, [field]: value };
      if (field === "make") {
        next.model = "";
      }
      return next;
    });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    const payload: Record<string, unknown> = {
      name: form.name,
      make: form.make,
      model: form.model || undefined,
      variant: form.variant || undefined,
      year_min: form.year_min ? parseInt(form.year_min) : undefined,
      year_max: form.year_max ? parseInt(form.year_max) : undefined,
      km_min: form.km_min ? parseInt(form.km_min) : undefined,
      km_max: form.km_max ? parseInt(form.km_max) : undefined,
      price_min: form.price_min ? parseInt(form.price_min) : undefined,
      price_max: form.price_max ? parseInt(form.price_max) : undefined,
      fuel_type: form.fuel_type || undefined,
      transmission: form.transmission || undefined,
    };

    try {
      if (initialData?.id) {
        await updateSearch(initialData.id, payload);
      } else {
        await createSearch(payload);
      }
      onSaved();
    } catch {
      setError("Er is een fout opgetreden. Probeer het opnieuw.");
    } finally {
      setLoading(false);
    }
  };

  const currentYear = new Date().getFullYear();
  const years = Array.from({ length: 30 }, (_, i) => currentYear - i);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4">
      <div className="max-h-[90vh] w-full max-w-lg overflow-y-auto rounded-xl bg-slate-800 p-6 shadow-2xl">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-lg font-bold text-white">
            {initialData?.id ? "Zoekopdracht bewerken" : "Nieuwe zoekopdracht"}
          </h2>
          <button
            onClick={onClose}
            className="rounded-lg p-1 text-slate-400 hover:bg-slate-700 hover:text-white"
          >
            <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Name */}
          <div>
            <label className="mb-1 block text-sm font-medium text-slate-300">Naam</label>
            <input
              type="text"
              required
              value={form.name}
              onChange={(e) => handleChange("name", e.target.value)}
              placeholder="bijv. BMW 3 Serie Diesel"
              className="w-full rounded-lg border border-slate-600 bg-slate-700 px-3 py-2 text-sm text-white placeholder-slate-400 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
          </div>

          {/* Make + Model */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="mb-1 block text-sm font-medium text-slate-300">Merk</label>
              <select
                required
                value={form.make}
                onChange={(e) => handleChange("make", e.target.value)}
                className="w-full rounded-lg border border-slate-600 bg-slate-700 px-3 py-2 text-sm text-white focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
              >
                <option value="">Selecteer merk</option>
                {Object.keys(MAKES_MODELS).sort().map((make) => (
                  <option key={make} value={make}>
                    {make}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium text-slate-300">Model</label>
              <select
                value={form.model}
                onChange={(e) => handleChange("model", e.target.value)}
                disabled={!form.make}
                className="w-full rounded-lg border border-slate-600 bg-slate-700 px-3 py-2 text-sm text-white disabled:opacity-50 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
              >
                <option value="">Alle modellen</option>
                {models.map((model) => (
                  <option key={model} value={model}>
                    {model}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Variant */}
          <div>
            <label className="mb-1 block text-sm font-medium text-slate-300">Variant (optioneel)</label>
            <input
              type="text"
              value={form.variant}
              onChange={(e) => handleChange("variant", e.target.value)}
              placeholder="bijv. 320d, GTI, AMG"
              className="w-full rounded-lg border border-slate-600 bg-slate-700 px-3 py-2 text-sm text-white placeholder-slate-400 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
          </div>

          {/* Year range */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="mb-1 block text-sm font-medium text-slate-300">Bouwjaar van</label>
              <select
                value={form.year_min}
                onChange={(e) => handleChange("year_min", e.target.value)}
                className="w-full rounded-lg border border-slate-600 bg-slate-700 px-3 py-2 text-sm text-white focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
              >
                <option value="">Geen minimum</option>
                {years.map((y) => (
                  <option key={y} value={y}>{y}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium text-slate-300">Bouwjaar tot</label>
              <select
                value={form.year_max}
                onChange={(e) => handleChange("year_max", e.target.value)}
                className="w-full rounded-lg border border-slate-600 bg-slate-700 px-3 py-2 text-sm text-white focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
              >
                <option value="">Geen maximum</option>
                {years.map((y) => (
                  <option key={y} value={y}>{y}</option>
                ))}
              </select>
            </div>
          </div>

          {/* KM range */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="mb-1 block text-sm font-medium text-slate-300">KM van</label>
              <input
                type="number"
                value={form.km_min}
                onChange={(e) => handleChange("km_min", e.target.value)}
                placeholder="0"
                className="w-full rounded-lg border border-slate-600 bg-slate-700 px-3 py-2 text-sm text-white placeholder-slate-400 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium text-slate-300">KM tot</label>
              <input
                type="number"
                value={form.km_max}
                onChange={(e) => handleChange("km_max", e.target.value)}
                placeholder="200000"
                className="w-full rounded-lg border border-slate-600 bg-slate-700 px-3 py-2 text-sm text-white placeholder-slate-400 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
              />
            </div>
          </div>

          {/* Price range */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="mb-1 block text-sm font-medium text-slate-300">Prijs van</label>
              <input
                type="number"
                value={form.price_min}
                onChange={(e) => handleChange("price_min", e.target.value)}
                placeholder="0"
                className="w-full rounded-lg border border-slate-600 bg-slate-700 px-3 py-2 text-sm text-white placeholder-slate-400 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium text-slate-300">Prijs tot</label>
              <input
                type="number"
                value={form.price_max}
                onChange={(e) => handleChange("price_max", e.target.value)}
                placeholder="50000"
                className="w-full rounded-lg border border-slate-600 bg-slate-700 px-3 py-2 text-sm text-white placeholder-slate-400 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
              />
            </div>
          </div>

          {/* Fuel + Transmission */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="mb-1 block text-sm font-medium text-slate-300">Brandstof</label>
              <select
                value={form.fuel_type}
                onChange={(e) => handleChange("fuel_type", e.target.value)}
                className="w-full rounded-lg border border-slate-600 bg-slate-700 px-3 py-2 text-sm text-white focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
              >
                <option value="">Alle</option>
                {FUEL_TYPES.map((f) => (
                  <option key={f} value={f}>{f}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium text-slate-300">Transmissie</label>
              <select
                value={form.transmission}
                onChange={(e) => handleChange("transmission", e.target.value)}
                className="w-full rounded-lg border border-slate-600 bg-slate-700 px-3 py-2 text-sm text-white focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
              >
                <option value="">Alle</option>
                {TRANSMISSIONS.map((t) => (
                  <option key={t} value={t}>{t}</option>
                ))}
              </select>
            </div>
          </div>

          {error && (
            <p className="text-sm text-red-400">{error}</p>
          )}

          <div className="flex gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 rounded-lg border border-slate-600 px-4 py-2 text-sm font-medium text-slate-300 hover:bg-slate-700"
            >
              Annuleren
            </button>
            <button
              type="submit"
              disabled={loading}
              className="flex-1 rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-500 disabled:opacity-50"
            >
              {loading ? "Opslaan..." : initialData?.id ? "Bijwerken" : "Aanmaken"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
