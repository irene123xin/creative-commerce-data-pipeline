with ranked as (
    select o.*,
           row_number() over (partition by customer_id order by order_at) as order_number,
           lag(order_at) over (partition by customer_id order by order_at) as previous_order_at
    from {{ ref('stg_orders') }} o
    where status = 'completed'
)
select * from ranked

