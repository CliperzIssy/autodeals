"use client";

import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import Image from "next/image";
import { getListingDetail } from "@/lib/api";
import DealBadge from "@/components/DealBadge";
import RedFlagBadge from "@/components/RedFlagBadge";
import ContactReveal from "@/components/ContactReveal";

function formatPrice(price: number): string {
  return (
    "\u20AC" +
    price.toLocaleString("de-DE", { minimumFractionDigits: 0, maximumFractionDigits: 0 })
  );
}

function formatKm(km: number): string {
  return km.toLocaleString("de-DE") + " km";
}

export default function ListingDetailPage() {
  const params = useParams();
  const router = useRouter();
  const listingId = params.id as string;

  const [listing, setListing] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [activeImage, setActiveImage] = useState(0);

  useEffect(() => {
    async function load() {
      try {
        const data = await getListingDetail(listingId);
        setListing(data);
      } catch {
        // error
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [listingId]);

  if (loading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-blue-500 border-t-transparent" />
      </div>
    );
  }

  if (!listing) {
    return (
      <div className="rounded-xl bg-slate-800 p-8 text-center">
        <p className="text-slate-400">Advertentie niet gevonden.</p>
        <button onClick={() => router.back()} className="mt-4 text-blue-400 hover:underline">
          Terug
        </button>
      </div>
    );
  }

  const images: string[] = listing.image_urls || listing.images || [];
  const priceDiff = listing.price_diff;
  const redFlags = listing.red_flags || [];

  return (
    <div className="space-y-6">
      {/* Back button */}
      <button
        onClick={() => router.back()}
        className="inline-flex items-center gap-1 text-sm text-slate-400 hover:text-white"
      >
        <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 19.5L8.25 12l7.5-7.5" />
        </svg>
        Terug naar resultaten
      </button>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Left column: Images + Details */}
        <div className="space-y-4 lg:col-span-2">
          {/* Image Gallery */}
          <div className="overflow-hidden rounded-xl bg-slate-800">
            <div className="relative aspect-[16/10] w-full bg-slate-700">
              {images.length > 0 ? (
                <Image
                  src={images[activeImage]}
                  alt={listing.title}
                  fill
                  className="object-cover"
                  sizes="(max-width: 1024px) 100vw, 66vw"
                />
              ) : (
                <div className="flex h-full items-center justify-center text-slate-500">
                  <svg className="h-20 w-20" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                  </svg>
                </div>
              )}
            </div>
            {images.length > 1 && (
              <div className="flex gap-2 overflow-x-auto p-3">
                {images.map((img: string, i: number) => (
                  <button
                    key={i}
                    onClick={() => setActiveImage(i)}
                    className={`relative h-16 w-20 shrink-0 overflow-hidden rounded-lg ${
                      i === activeImage ? "ring-2 ring-blue-500" : "opacity-60 hover:opacity-100"
                    }`}
                  >
                    <Image src={img} alt="" fill className="object-cover" sizes="80px" />
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* AI Summary */}
          {(listing.ai_summary || listing.summary) && (
            <div className="rounded-xl bg-slate-800 p-5">
              <h2 className="mb-2 flex items-center gap-2 text-sm font-semibold text-blue-400">
                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.455 2.456L21.75 6l-1.036.259a3.375 3.375 0 00-2.455 2.456z" />
                </svg>
                AI Samenvatting
              </h2>
              <p className="text-sm leading-relaxed text-slate-300">
                {listing.ai_summary || listing.summary}
              </p>
            </div>
          )}

          {/* Red Flags */}
          {redFlags.length > 0 && (
            <div className="rounded-xl bg-slate-800 p-5">
              <h2 className="mb-3 text-sm font-semibold text-red-400">
                Waarschuwingen ({redFlags.length})
              </h2>
              <RedFlagBadge flags={redFlags} />
            </div>
          )}

          {/* Vehicle Details */}
          <div className="rounded-xl bg-slate-800 p-5">
            <h2 className="mb-3 text-sm font-semibold text-slate-300">Voertuiggegevens</h2>
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
              {listing.year && (
                <div>
                  <p className="text-xs text-slate-500">Bouwjaar</p>
                  <p className="text-sm font-medium">{listing.year}</p>
                </div>
              )}
              {listing.km !== undefined && listing.km !== null && (
                <div>
                  <p className="text-xs text-slate-500">Kilometerstand</p>
                  <p className="text-sm font-medium">{formatKm(listing.km)}</p>
                </div>
              )}
              {listing.fuel_type && (
                <div>
                  <p className="text-xs text-slate-500">Brandstof</p>
                  <p className="text-sm font-medium">{listing.fuel_type}</p>
                </div>
              )}
              {listing.transmission && (
                <div>
                  <p className="text-xs text-slate-500">Transmissie</p>
                  <p className="text-sm font-medium">{listing.transmission}</p>
                </div>
              )}
              {listing.power && (
                <div>
                  <p className="text-xs text-slate-500">Vermogen</p>
                  <p className="text-sm font-medium">{listing.power}</p>
                </div>
              )}
              {listing.color && (
                <div>
                  <p className="text-xs text-slate-500">Kleur</p>
                  <p className="text-sm font-medium">{listing.color}</p>
                </div>
              )}
              {listing.location && (
                <div>
                  <p className="text-xs text-slate-500">Locatie</p>
                  <p className="text-sm font-medium">{listing.location}</p>
                </div>
              )}
              {listing.source && (
                <div>
                  <p className="text-xs text-slate-500">Bron</p>
                  <p className="text-sm font-medium">{listing.source}</p>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Right column: Price + Actions */}
        <div className="space-y-4">
          {/* Price Card */}
          <div className="rounded-xl bg-slate-800 p-5">
            <h3 className="truncate text-lg font-bold text-white">{listing.title}</h3>

            <div className="mt-3">
              <p className="text-3xl font-bold text-white">{formatPrice(listing.price)}</p>

              {priceDiff !== null && priceDiff !== undefined && (
                <p
                  className={`mt-1 text-sm font-medium ${
                    priceDiff < 0 ? "text-green-400" : priceDiff > 0 ? "text-red-400" : "text-slate-400"
                  }`}
                >
                  {priceDiff < 0
                    ? `${formatPrice(Math.abs(priceDiff))} onder marktgemiddelde`
                    : priceDiff > 0
                    ? `${formatPrice(priceDiff)} boven marktgemiddelde`
                    : "Gelijk aan marktgemiddelde"}
                </p>
              )}
            </div>

            <div className="mt-3">
              <DealBadge score={listing.deal_score ?? null} size="lg" />
            </div>

            {/* Price vs Market Bar */}
            {listing.market_avg_price && (
              <div className="mt-4 space-y-2">
                <p className="text-xs text-slate-400">Prijs vs. markt</p>
                <div className="relative h-6 rounded-full bg-slate-700">
                  {(() => {
                    const ratio = Math.min(
                      (listing.price / listing.market_avg_price) * 100,
                      150
                    );
                    const barColor =
                      ratio < 90
                        ? "bg-green-500"
                        : ratio < 110
                        ? "bg-yellow-500"
                        : "bg-red-500";
                    return (
                      <>
                        <div
                          className={`h-full rounded-full ${barColor}`}
                          style={{ width: `${Math.min(ratio, 100)}%` }}
                        />
                        <div
                          className="absolute top-0 h-full w-0.5 bg-white/60"
                          style={{ left: "66.67%" }}
                          title="Marktgemiddelde"
                        />
                      </>
                    );
                  })()}
                </div>
                <div className="flex justify-between text-xs text-slate-500">
                  <span>Vraagprijs: {formatPrice(listing.price)}</span>
                  <span>Markt: {formatPrice(listing.market_avg_price)}</span>
                </div>
              </div>
            )}
          </div>

          {/* BPM + Total Cost */}
          {(listing.bpm_estimate || listing.total_cost_estimate) && (
            <div className="rounded-xl bg-slate-800 p-5">
              <h3 className="mb-3 text-sm font-semibold text-slate-300">
                Kostenraming Nederland
              </h3>
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-slate-400">Aankoopprijs</span>
                  <span className="font-medium">{formatPrice(listing.price)}</span>
                </div>
                {listing.bpm_estimate && (
                  <div className="flex justify-between text-sm">
                    <span className="text-slate-400">BPM (geschat)</span>
                    <span className="font-medium text-orange-400">
                      + {formatPrice(listing.bpm_estimate)}
                    </span>
                  </div>
                )}
                {listing.transport_cost && (
                  <div className="flex justify-between text-sm">
                    <span className="text-slate-400">Transport (geschat)</span>
                    <span className="font-medium">+ {formatPrice(listing.transport_cost)}</span>
                  </div>
                )}
                <div className="border-t border-slate-700 pt-2">
                  <div className="flex justify-between text-sm font-semibold">
                    <span className="text-slate-300">Totaal geschat</span>
                    <span className="text-white">
                      {formatPrice(
                        listing.total_cost_estimate ||
                          listing.price +
                            (listing.bpm_estimate || 0) +
                            (listing.transport_cost || 0)
                      )}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Seller / Contact */}
          <div className="rounded-xl bg-slate-800 p-5">
            <h3 className="mb-3 text-sm font-semibold text-slate-300">Verkoper</h3>
            <ContactReveal
              listingId={listingId}
              existingPhone={listing.seller_phone || listing.phone}
              sellerName={listing.seller_name || listing.dealer_name}
            />
          </div>

          {/* Link to original */}
          {listing.source_url && (
            <a
              href={listing.source_url}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center justify-center gap-2 rounded-xl border border-slate-600 bg-slate-800 p-3 text-sm font-medium text-slate-300 hover:bg-slate-700 hover:text-white"
            >
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 6H5.25A2.25 2.25 0 003 8.25v10.5A2.25 2.25 0 005.25 21h10.5A2.25 2.25 0 0018 18.75V10.5m-10.5 6L21 3m0 0h-5.25M21 3v5.25" />
              </svg>
              Open originele advertentie
            </a>
          )}
        </div>
      </div>
    </div>
  );
}
