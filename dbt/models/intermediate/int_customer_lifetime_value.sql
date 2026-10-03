select c.customer_id, c.signup_date, c.acquisition_channel, c.region,
       count(o.order_id) as completed_orders,
       coalesce(sum(o.revenue), 0) as observed_lifetime_revenue,
       coalesce(avg(o.revenue), 0) as average_order_value,
       min(o.order_at) as first_order_at,
       max(o.order_at) as latest_order_at
from {{ ref('stg_customers') }} c
left join {{ ref('stg_orders') }} o
  on c.customer_id = o.customer_id and o.status = 'completed'
group by 1,2,3,4
