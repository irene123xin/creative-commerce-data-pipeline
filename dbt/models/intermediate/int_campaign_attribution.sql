with order_revenue as (
    select coalesce(campaign_id, 'DIRECT_OR_UNKNOWN') as campaign_id,
           count(*) as attributed_orders, sum(revenue) as attributed_revenue,
           count(distinct customer_id) as acquired_customers
    from {{ ref('stg_orders') }}
    where status = 'completed'
    group by 1
), campaign_base as (
    select campaign_id, campaign_name, channel, spend, impressions, clicks,
           reported_conversions, start_date, end_date from {{ ref('stg_campaigns') }}
    union all
    select 'DIRECT_OR_UNKNOWN', 'Direct or unknown', 'direct_or_unknown', 0, 0, 0, 0,
           null::date, null::date
)
select c.*, coalesce(o.attributed_orders, 0) as attributed_orders,
       coalesce(o.attributed_revenue, 0) as attributed_revenue,
       coalesce(o.acquired_customers, 0) as acquired_customers
from campaign_base c
left join order_revenue o using (campaign_id)
