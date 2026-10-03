select p.product_id, p.product_name, p.category, p.price, p.cost,
       count(distinct case when o.status = 'completed' then o.order_id end) as completed_orders,
       coalesce(sum(case when o.status = 'completed' then i.quantity else 0 end), 0) as units_sold,
       coalesce(sum(case when o.status = 'completed' then i.gross_revenue else 0 end), 0) as gross_revenue,
       coalesce(sum(case when o.status = 'completed' then i.gross_margin else 0 end), 0) as gross_margin,
       count(distinct case when o.status = 'completed' then o.customer_id end) as unique_customers
from {{ ref('stg_products') }} p
left join {{ ref('stg_order_items') }} i using (product_id)
left join {{ ref('stg_orders') }} o using (order_id)
group by 1,2,3,4,5

