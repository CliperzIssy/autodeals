import axios from "axios";

const api = axios.create({
  baseURL: "http://localhost:8000",
  headers: {
    "Content-Type": "application/json",
  },
});

// Auth interceptor
api.interceptors.request.use((config) => {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("autodeals_token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

// Response interceptor for 401
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401 && typeof window !== "undefined") {
      localStorage.removeItem("autodeals_token");
      window.location.href = "/login";
    }
    return Promise.reject(error);
  }
);

const SORT_MAP: Record<string, string> = {
  score: "score_desc",
  km: "km_asc",
};

const FUEL_MAP: Record<string, string> = {
  benzine: "petrol",
  diesel: "diesel",
  elektrisch: "electric",
  hybride: "hybrid",
  "plug-in hybride": "plugin_hybrid",
  lpg: "lpg",
  petrol: "petrol",
  electric: "electric",
  hybrid: "hybrid",
  plugin_hybrid: "plugin_hybrid",
};

const TRANSMISSION_MAP: Record<string, string> = {
  handgeschakeld: "manual",
  automaat: "automatic",
  manual: "manual",
  automatic: "automatic",
};

const MAKE_MAP: Record<string, string> = {
  audi: "audi",
  bmw: "bmw",
  citroen: "citroen",
  fiat: "fiat",
  ford: "ford",
  honda: "honda",
  hyundai: "hyundai",
  jaguar: "jaguar",
  kia: "kia",
  "land rover": "land rover",
  mazda: "mazda",
  "mercedes-benz": "mercedes-benz",
  "mercedes benz": "mercedes-benz",
  mini: "mini",
  mitsubishi: "mitsubishi",
  nissan: "nissan",
  opel: "opel",
  peugeot: "peugeot",
  porsche: "porsche",
  renault: "renault",
  seat: "seat",
  skoda: "skoda",
  subaru: "subaru",
  suzuki: "suzuki",
  tesla: "tesla",
  toyota: "toyota",
  volkswagen: "volkswagen",
  volvo: "volvo",
};

const DISPLAY_MAKE_MAP: Record<string, string> = {
  "mercedes-benz": "Mercedes-Benz",
  volkswagen: "Volkswagen",
  bmw: "BMW",
  audi: "Audi",
  citroen: "Citroën",
  fiat: "Fiat",
  ford: "Ford",
  honda: "Honda",
  hyundai: "Hyundai",
  jaguar: "Jaguar",
  kia: "Kia",
  "land rover": "Land Rover",
  mazda: "Mazda",
  mini: "MINI",
  mitsubishi: "Mitsubishi",
  nissan: "Nissan",
  opel: "Opel",
  peugeot: "Peugeot",
  porsche: "Porsche",
  renault: "Renault",
  seat: "SEAT",
  skoda: "Skoda",
  subaru: "Subaru",
  suzuki: "Suzuki",
  tesla: "Tesla",
  toyota: "Toyota",
  volvo: "Volvo",
};

const MODEL_MAP_BY_MAKE: Record<string, Record<string, string>> = {
  bmw: {
    "1 serie": "1er",
    "2 serie": "2er",
    "3 serie": "3er",
    "4 serie": "4er",
    "5 serie": "5er",
    "7 serie": "7er",
  },
  "mercedes-benz": {
    "a-klasse": "a-klasse",
    "b-klasse": "b-klasse",
    "c-klasse": "c-klasse",
    "e-klasse": "e-klasse",
    "s-klasse": "s-klasse",
  },
};

function normalizeText(value: string): string {
  return value
    .normalize("NFKD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .trim()
    .replace(/\s+/g, " ");
}

function eurosToCents(value: unknown): number | undefined {
  if (value === undefined || value === null || value === "") {
    return undefined;
  }
  const num = Number(value);
  if (!Number.isFinite(num)) {
    return undefined;
  }
  return Math.round(num * 100);
}

function centsToEuros(value: unknown): number | null {
  if (value === undefined || value === null || value === "") {
    return null;
  }
  const num = Number(value);
  if (!Number.isFinite(num)) {
    return null;
  }
  return Math.round(num / 100);
}

function toCanonicalMake(value: unknown): string | undefined {
  if (!value || typeof value !== "string") return undefined;
  const key = normalizeText(value);
  return MAKE_MAP[key] || key;
}

function toCanonicalModel(make: string | undefined, model: unknown): string | undefined {
  if (!model || typeof model !== "string") return undefined;
  const key = normalizeText(model);
  if (!make) return key;
  return MODEL_MAP_BY_MAKE[make]?.[key] || key;
}

function toKmBucket(kmMin?: number, kmMax?: number): string | undefined {
  if (kmMin === 0 && kmMax === 50_000) return "0-50k";
  if (kmMin === 50_000 && kmMax === 100_000) return "50-100k";
  if (kmMin === 100_000 && kmMax === 150_000) return "100-150k";
  if (kmMin === 150_000 && kmMax === undefined) return "150k+";
  return undefined;
}

function normalizeImageUrls(input: unknown): string[] {
  if (Array.isArray(input)) {
    return input.filter((v): v is string => typeof v === "string" && v.length > 0);
  }
  if (input && typeof input === "object") {
    const obj = input as Record<string, unknown>;
    if (Array.isArray(obj.images)) {
      return obj.images.filter((v): v is string => typeof v === "string" && v.length > 0);
    }
    if (Array.isArray(obj.urls)) {
      return obj.urls.filter((v): v is string => typeof v === "string" && v.length > 0);
    }
  }
  return [];
}

function normalizeRedFlags(input: unknown): Array<{ type: string; severity: "high" | "medium" | "low"; description: string }> {
  if (!input) return [];

  if (Array.isArray(input)) {
    return input
      .map((entry) => {
        if (typeof entry === "string") {
          return { type: "warning", severity: "medium" as const, description: entry };
        }
        if (entry && typeof entry === "object") {
          const e = entry as Record<string, unknown>;
          const severityRaw = String(e.severity || "medium").toLowerCase();
          const severity = severityRaw === "high" || severityRaw === "low" ? severityRaw : "medium";
          return {
            type: String(e.type || "warning"),
            severity,
            description: String(e.description || e.message || "AI flag"),
          };
        }
        return null;
      })
      .filter((v): v is { type: string; severity: "high" | "medium" | "low"; description: string } => Boolean(v));
  }

  if (typeof input === "object") {
    return Object.entries(input as Record<string, unknown>).map(([key, value]) => ({
      type: key,
      severity: "medium",
      description: typeof value === "string" ? value : JSON.stringify(value),
    }));
  }

  return [];
}

function mapListing(raw: Record<string, unknown>): any {
  const price = centsToEuros(raw.price_cents) ?? 0;
  const marketAvgPrice = centsToEuros(raw.ai_market_avg_price_cents);
  const priceDiff = centsToEuros(raw.ai_price_diff_cents);
  const redFlags = normalizeRedFlags(raw.ai_red_flags || raw.red_flags);
  const imageUrls = normalizeImageUrls(raw.image_urls || raw.images);

  const sellerZip = typeof raw.seller_zip === "string" ? raw.seller_zip : "";
  const sellerCity = typeof raw.seller_city === "string" ? raw.seller_city : "";
  const location =
    (typeof raw.location === "string" && raw.location) ||
    `${sellerZip} ${sellerCity}`.trim() ||
    null;

  const powerHp = raw.power_hp !== undefined && raw.power_hp !== null ? Number(raw.power_hp) : null;
  const powerKw = raw.power_kw !== undefined && raw.power_kw !== null ? Number(raw.power_kw) : null;

  return {
    ...raw,
    id: raw.id,
    title:
      (raw.title as string) ||
      [raw.make, raw.model, raw.variant].filter(Boolean).join(" ") ||
      "Onbekende advertentie",
    price,
    market_avg_price: marketAvgPrice,
    price_diff: priceDiff,
    deal_score: (raw.deal_score as number | null | undefined) ?? (raw.ai_deal_score as number | null | undefined) ?? null,
    summary: raw.summary || raw.ai_dutch_summary || null,
    ai_summary: raw.ai_summary || raw.ai_dutch_summary || null,
    red_flags: redFlags,
    location,
    images: imageUrls,
    image_urls: imageUrls,
    power: powerHp ? `${powerHp} pk` : powerKw ? `${powerKw} kW` : null,
    bpm_estimate: centsToEuros(raw.estimated_bpm_cents),
    total_cost_estimate: centsToEuros(raw.estimated_total_cost_cents),
    transport_cost: null,
  };
}

function mapSearch(raw: Record<string, unknown>): any {
  const make = typeof raw.make === "string" ? raw.make : "";
  const makeDisplay = DISPLAY_MAKE_MAP[normalizeText(make)] || make;
  return {
    ...raw,
    make: makeDisplay,
    model: raw.model || "",
    last_scan_at: raw.last_scan_at || raw.last_scanned_at || null,
    price_min: centsToEuros(raw.price_min),
    price_max: centsToEuros(raw.price_max),
  };
}

function normalizeSearchPayload(data: Record<string, unknown>): Record<string, unknown> {
  const make = toCanonicalMake(data.make);
  const model = toCanonicalModel(make, data.model);
  const fuel = typeof data.fuel_type === "string" ? FUEL_MAP[normalizeText(data.fuel_type)] || normalizeText(data.fuel_type) : undefined;
  const transmission =
    typeof data.transmission === "string"
      ? TRANSMISSION_MAP[normalizeText(data.transmission)] || normalizeText(data.transmission)
      : undefined;

  return {
    ...data,
    make: make || data.make,
    model,
    fuel_type: fuel,
    transmission,
    price_min: eurosToCents(data.price_min),
    price_max: eurosToCents(data.price_max),
  };
}

// Auth
export async function login(email: string, password: string) {
  const res = await api.post("/api/auth/login", { email, password });
  return res.data;
}

export async function register(data: {
  name: string;
  email: string;
  password: string;
  company_name?: string;
}) {
  const res = await api.post("/api/auth/register", data);
  return res.data;
}

// Dashboard
export async function getDashboardStats() {
  const res = await api.get("/api/dashboard/stats");
  const data = res.data || {};
  const topDeals = Array.isArray(data.top_deals) ? data.top_deals : [];
  return {
    ...data,
    new_listings_today: data.new_listings_today ?? data.new_today ?? 0,
    top_deals: typeof data.top_deals === "number" ? data.top_deals : topDeals.length,
  };
}

export async function getRecentDeals() {
  const res = await api.get("/api/dashboard/recent-deals");
  const rows = Array.isArray(res.data) ? res.data : [];
  return {
    listings: rows.map((row) => mapListing(row)),
  };
}

// Searches
export async function getSearches(): Promise<any[]> {
  const res = await api.get("/api/searches/");
  const rows = Array.isArray(res.data) ? res.data : [];
  return rows.map((row) => mapSearch(row));
}

export async function getSearch(id: string) {
  const res = await api.get(`/api/searches/${id}`);
  return mapSearch(res.data || {});
}

export async function createSearch(data: Record<string, unknown>) {
  const res = await api.post("/api/searches/", normalizeSearchPayload(data));
  return res.data;
}

export async function updateSearch(id: string, data: Record<string, unknown>) {
  const res = await api.put(`/api/searches/${id}`, normalizeSearchPayload(data));
  return res.data;
}

export async function deleteSearch(id: string) {
  const res = await api.delete(`/api/searches/${id}`);
  return res.data;
}

export async function triggerScan(searchId: string) {
  const res = await api.post(`/api/searches/${searchId}/scan`);
  return res.data;
}

// Listings
export async function getSearchListings(
  searchId: string,
  params?: {
    sort?: string;
    km_min?: number;
    km_max?: number;
    min_score?: number;
    page?: number;
    per_page?: number;
  }
): Promise<any> {
  const sortBy = params?.sort ? SORT_MAP[params.sort] || params.sort : undefined;
  const kmBucket = toKmBucket(params?.km_min, params?.km_max);

  const backendParams: Record<string, unknown> = {
    sort_by: sortBy,
    km_bucket: kmBucket,
    min_score: params?.min_score,
    page: params?.page,
    per_page: params?.per_page,
  };

  const res = await api.get(`/api/listings/search/${searchId}`, {
    params: backendParams,
  });

  const data = res.data || {};
  const rows = Array.isArray(data.items) ? data.items : [];

  return {
    listings: rows.map((row: Record<string, unknown>) => mapListing(row)),
    total: data.total || 0,
    page: data.page || 1,
    per_page: data.per_page || 25,
    total_pages: data.pages || 1,
    km_counts: data.km_counts || undefined,
  };
}

export async function getListingDetail(id: string) {
  const res = await api.get(`/api/listings/${id}`);
  return mapListing(res.data || {});
}

// Contact
export async function scrapeContact(listingId: string) {
  const res = await api.post(`/api/listings/${listingId}/contact`);
  return res.data;
}

export default api;
