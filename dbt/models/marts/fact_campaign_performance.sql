select campaign_id, channel, spend, impressions, clicks, reported_conversions,
       attributed_orders, attributed_revenue, acquired_customers,
       attributed_revenue / nullif(spend, 0) as roas,
       spend / nullif(acquired_customers, 0) as customer_acquisition_cost,
       attributed_orders::numeric / nullif(clicks, 0) as conversion_rate
from {{ ref('int_campaign_attribution') }}

