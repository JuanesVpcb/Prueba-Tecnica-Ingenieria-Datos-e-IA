from __future__ import annotations

from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator

from src.data.models import ChannelEnum


CHANNEL_MAPPING = {
    "fb ads": ChannelEnum.FACEBOOK,
    "facebook_ads": ChannelEnum.FACEBOOK,
    "facebook": ChannelEnum.FACEBOOK,
    "google ads": ChannelEnum.GOOGLE,
    "google_ads": ChannelEnum.GOOGLE,
    "google": ChannelEnum.GOOGLE,
    "instagram": ChannelEnum.INSTAGRAM,
    "ig": ChannelEnum.INSTAGRAM,
    "email": ChannelEnum.EMAIL,
    "direct": ChannelEnum.DIRECT,
}


def normalize_channel(channel: str) -> ChannelEnum:
    normalized = channel.strip().lower()
    return CHANNEL_MAPPING.get(normalized, ChannelEnum.OTHER)


class SaleRecord(BaseModel):
    transaction_id: str = Field(min_length=1)
    customer_id: str = Field(min_length=1)
    amount: Decimal
    sale_date: date
    channel: str

    @field_validator("amount")
    @classmethod
    def amount_must_be_non_negative(cls, value: Decimal) -> Decimal:
        if value < 0:
            raise ValueError("amount must be non-negative")
        return value

    @field_validator("sale_date")
    @classmethod
    def sale_date_not_future(cls, value: date) -> date:
        if value > date.today():
            raise ValueError("sale_date cannot be in the future")
        return value


class MarketingRecord(BaseModel):
    spend_date: date
    channel: str
    campaign_name: str = Field(min_length=1)
    campaign_cost: Decimal
    impressions: int
    clicks: int

    @field_validator("campaign_cost")
    @classmethod
    def cost_must_be_non_negative(cls, value: Decimal) -> Decimal:
        if value < 0:
            raise ValueError("campaign_cost must be non-negative")
        return value

    @field_validator("spend_date")
    @classmethod
    def spend_date_not_future(cls, value: date) -> date:
        if value > date.today():
            raise ValueError("spend_date cannot be in the future")
        return value

    @field_validator("impressions", "clicks")
    @classmethod
    def metrics_non_negative(cls, value: int) -> int:
        if value < 0:
            raise ValueError("impressions/clicks must be non-negative")
        return value


def validate_sales(records: list[dict]) -> list[SaleRecord]:
    return [SaleRecord(**record) for record in records]


def validate_marketing(records: list[dict]) -> list[MarketingRecord]:
    return [MarketingRecord(**record) for record in records]
