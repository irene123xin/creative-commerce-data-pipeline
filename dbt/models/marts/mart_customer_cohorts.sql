with completed_orders as (
    select customer_id, order_at
    from {{ ref('stg_orders') }}
    where status = 'completed'
), cohorts as (
    select customer_id, date_trunc('month', min(order_at))::date as cohort_month
    from completed_orders group by 1
), activity as (
    select c.cohort_month, date_trunc('month', o.order_at)::date as activity_month,
           ((extract(year from age(date_trunc('month', o.order_at), c.cohort_month)) * 12)
             + extract(month from age(date_trunc('month', o.order_at), c.cohort_month)))::int as month_number,
           count(distinct o.customer_id) as active_customers
    from cohorts c join completed_orders o using (customer_id)
    group by 1,2,3
), sizes as (
    select cohort_month, count(*) as cohort_size from cohorts group by 1
)
select a.*, s.cohort_size, a.active_customers::numeric / nullif(s.cohort_size, 0) as retention_rate
from activity a join sizes s using (cohort_month)
