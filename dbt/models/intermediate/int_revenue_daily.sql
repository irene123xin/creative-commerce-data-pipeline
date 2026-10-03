{{ config(materialized='incremental', unique_key='order_date') }}

select order_at::date as order_date,
       count(*) as orders,
       sum(revenue) as revenue,
       avg(revenue) as average_order_value,
       count(distinct customer_id) as purchasing_customers
from {{ ref('stg_orders') }}
where status = 'completed'
{% if is_incremental() %}
  and order_at::date >= (select coalesce(max(order_date), '1900-01-01') from {{ this }})
{% endif %}
group by 1
