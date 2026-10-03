from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st
from sqlalchemy import create_engine, text

from pipeline.utils.config import settings

st.set_page_config(page_title="Creative Commerce Intelligence", layout="wide")
st.markdown("""
<style>
.stApp { background:#ffffff; color:#17211d; }
h1 { letter-spacing:-.035em; }
[data-testid="stSidebar"] { background:#f5f6f4; border-right:1px solid #dfe4e1; }
[data-testid="stMetric"] { border-top:2px solid #dfe4e1; padding-top:.8rem; }
.stButton button { border-radius:5px; }
</style>""", unsafe_allow_html=True)


@st.cache_resource
def engine():
    return create_engine(settings.database_url, future=True)


@st.cache_data(ttl=120)
def query(sql: str) -> pd.DataFrame:
    with engine().connect() as connection:
        return pd.read_sql(text(sql), connection)


page = st.sidebar.radio("View", ["Overview", "Campaigns", "Customers", "Products", "Funnel"])
st.title(page)
st.caption("Synthetic commerce data · analytics marts produced by dbt")

try:
    if page == "Overview":
        daily = query("select * from analytics.mart_revenue_daily order by order_date")
        customers = query("select * from analytics.mart_customer_ltv")
        total_revenue = daily["revenue"].sum()
        total_orders = daily["orders"].sum()
        cols = st.columns(4)
        cols[0].metric("Revenue", f"${total_revenue:,.0f}")
        cols[1].metric("Orders", f"{total_orders:,.0f}")
        cols[2].metric("Average order value", f"${total_revenue / max(total_orders, 1):,.2f}")
        cols[3].metric("Repeat purchase rate", f"{customers['is_repeat_customer'].mean():.1%}")
        st.plotly_chart(px.line(daily, x="order_date", y="revenue", title="Daily revenue"), width="stretch")
    elif page == "Campaigns":
        data = query("select * from analytics.mart_campaign_performance order by attributed_revenue desc")
        st.dataframe(data, width="stretch", hide_index=True)
        st.plotly_chart(px.scatter(data, x="spend", y="attributed_revenue", color="channel",
                                   size="attributed_orders", hover_name="campaign_id", title="Spend and attributed revenue"), width="stretch")
        st.caption("ROAS is attributed completed-order revenue divided by spend. CAC is spend divided by attributed customers.")
    elif page == "Customers":
        data = query("select * from analytics.mart_customer_ltv")
        cohorts = query("select * from analytics.mart_customer_cohorts")
        st.plotly_chart(px.box(data, x="acquisition_channel", y="observed_lifetime_revenue",
                               title="Observed customer revenue by acquisition channel"), width="stretch")
        st.caption("Observed customer value is historical completed-order revenue; it is not a prediction.")
        st.dataframe(cohorts, width="stretch", hide_index=True)
    elif page == "Products":
        data = query("select * from analytics.mart_product_performance order by gross_revenue desc")
        st.plotly_chart(px.bar(data.head(20), x="product_name", y="gross_revenue", color="category",
                               title="Top products by gross revenue"), width="stretch")
        st.dataframe(data, width="stretch", hide_index=True)
    else:
        data = query("select * from analytics.mart_conversion_funnel")
        stages = ["sessions", "product_views", "add_to_carts", "purchases"]
        funnel = pd.DataFrame({"stage": stages, "sessions": [data.iloc[0][stage] for stage in stages]})
        st.plotly_chart(px.funnel(funnel, x="sessions", y="stage", title="Session conversion funnel"), width="stretch")
except Exception as exc:
    st.error("Analytics marts are unavailable. Start PostgreSQL and run the pipeline before opening the dashboard.")
    st.caption(str(exc))
