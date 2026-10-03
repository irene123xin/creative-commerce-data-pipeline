select *,
       sum(revenue) over (order by order_date rows between unbounded preceding and current row) as cumulative_revenue,
       avg(revenue) over (order by order_date rows between 6 preceding and current row) as revenue_7_day_average
from {{ ref('int_revenue_daily') }}
