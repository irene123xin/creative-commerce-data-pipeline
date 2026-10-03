select *, gross_margin / nullif(gross_revenue, 0) as margin_rate,
       dense_rank() over (partition by category order by gross_revenue desc) as category_revenue_rank
from {{ ref('int_product_performance') }}

