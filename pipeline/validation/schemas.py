from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator


class CustomerRecord(BaseModel):
    customer_id: str = Field(pattern=r"^C\d+$")
    signup_date: date
    acquisition_channel: Literal["organic", "paid_search", "paid_social", "email", "referral"]
    region: Literal["Northeast", "South", "Midwest", "West"]
    age_group: Literal["18-24", "25-34", "35-44", "45-54", "55+"]


class ProductRecord(BaseModel):
    product_id: str = Field(pattern=r"^P\d+$")
    product_name: str
    category: str
    price: float = Field(ge=0)
    cost: float = Field(ge=0)

    @model_validator(mode="after")
    def price_covers_cost(self):
        if self.price < self.cost:
            raise ValueError("price must be greater than or equal to cost")
        return self


class OrderRecord(BaseModel):
    order_id: str = Field(pattern=r"^O\d+$")
    customer_id: str
    order_date: datetime
    status: Literal["completed", "refunded", "cancelled"]
    discount: float = Field(ge=0)
    revenue: float = Field(ge=0)
    campaign_id: str | None = None


class OrderItemRecord(BaseModel):
    order_item_id: str
    order_id: str
    product_id: str
    quantity: int = Field(ge=1)
    unit_price: float = Field(ge=0)
    unit_cost: float = Field(ge=0)


class CampaignRecord(BaseModel):
    campaign_id: str = Field(pattern=r"^M\d+$")
    campaign_name: str
    channel: Literal["paid_search", "paid_social", "email", "affiliate"]
    spend: float = Field(ge=0)
    impressions: int = Field(ge=0)
    clicks: int = Field(ge=0)
    conversions: int = Field(ge=0)
    start_date: date
    end_date: date

    @model_validator(mode="after")
    def valid_funnel(self):
        if self.clicks > self.impressions or self.conversions > self.clicks:
            raise ValueError("campaign funnel counts are inconsistent")
        if self.end_date < self.start_date:
            raise ValueError("end_date precedes start_date")
        return self


class WebEventRecord(BaseModel):
    event_id: str
    customer_id: str | None = None
    anonymous_session_id: str
    timestamp: datetime
    event_type: Literal["session_start", "product_view", "add_to_cart", "purchase"]
    product_id: str | None = None
    campaign_id: str | None = None


SCHEMAS = {
    "customers": (CustomerRecord, "customer_id"),
    "products": (ProductRecord, "product_id"),
    "orders": (OrderRecord, "order_id"),
    "order_items": (OrderItemRecord, "order_item_id"),
    "campaigns": (CampaignRecord, "campaign_id"),
    "website_events": (WebEventRecord, "event_id"),
}
