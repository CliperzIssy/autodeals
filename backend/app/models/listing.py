import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Boolean, Integer, BigInteger, Float, Text, DateTime, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.database import Base


class Listing(Base):
    __tablename__ = "listings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source: Mapped[str] = mapped_column(String(20), nullable=False)
    source_id: Mapped[str] = mapped_column(String(255), nullable=False)
    source_url: Mapped[str] = mapped_column(Text, nullable=False)

    # Core vehicle data
    make: Mapped[str | None] = mapped_column(String(100))
    model: Mapped[str | None] = mapped_column(String(100))
    variant: Mapped[str | None] = mapped_column(String(200))
    year: Mapped[int | None] = mapped_column(Integer)
    month_registered: Mapped[int | None] = mapped_column(Integer)
    km: Mapped[int | None] = mapped_column(Integer)
    price_cents: Mapped[int | None] = mapped_column(BigInteger)
    currency: Mapped[str] = mapped_column(String(3), default="EUR")
    fuel_type: Mapped[str | None] = mapped_column(String(50))
    transmission: Mapped[str | None] = mapped_column(String(50))
    power_kw: Mapped[int | None] = mapped_column(Integer)
    power_hp: Mapped[int | None] = mapped_column(Integer)
    engine_size_cc: Mapped[int | None] = mapped_column(Integer)
    body_type: Mapped[str | None] = mapped_column(String(50))
    color: Mapped[str | None] = mapped_column(String(50))
    doors: Mapped[int | None] = mapped_column(Integer)

    # Seller info
    seller_type: Mapped[str | None] = mapped_column(String(20))
    seller_name: Mapped[str | None] = mapped_column(String(255))
    seller_city: Mapped[str | None] = mapped_column(String(100))
    seller_zip: Mapped[str | None] = mapped_column(String(20))
    seller_country: Mapped[str | None] = mapped_column(String(5))
    seller_phone: Mapped[str | None] = mapped_column(String(100))
    seller_phone_scraped_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Listing metadata
    title: Mapped[str | None] = mapped_column(Text)
    description: Mapped[str | None] = mapped_column(Text)
    thumbnail_url: Mapped[str | None] = mapped_column(Text)
    image_urls: Mapped[dict | None] = mapped_column(JSONB)
    listing_created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # AI-processed fields
    normalized_title: Mapped[str | None] = mapped_column(Text)
    ai_red_flags: Mapped[dict | None] = mapped_column(JSONB)
    ai_deal_score: Mapped[int | None] = mapped_column(Integer)
    ai_market_avg_price_cents: Mapped[int | None] = mapped_column(BigInteger)
    ai_price_diff_cents: Mapped[int | None] = mapped_column(BigInteger)
    ai_dutch_summary: Mapped[str | None] = mapped_column(Text)
    ai_processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # BPM estimation
    estimated_bpm_cents: Mapped[int | None] = mapped_column(BigInteger)
    estimated_total_cost_cents: Mapped[int | None] = mapped_column(BigInteger)

    # Dedup & tracking
    content_hash: Mapped[str | None] = mapped_column(String(64))
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint("source", "source_id", name="uq_listing_source"),
        Index("idx_listings_source_id", "source", "source_id"),
        Index("idx_listings_make_model", "make", "model", "year"),
        Index("idx_listings_deal_score", "ai_deal_score", postgresql_where="ai_deal_score > 70"),
        Index("idx_listings_active", "is_active", postgresql_where="is_active = true"),
        Index("idx_listings_price", "price_cents", postgresql_where="is_active = true"),
    )


class SearchListing(Base):
    __tablename__ = "search_listings"

    search_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("searches.id", ondelete="CASCADE"), primary_key=True)
    listing_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("listings.id", ondelete="CASCADE"), primary_key=True)
    matched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
