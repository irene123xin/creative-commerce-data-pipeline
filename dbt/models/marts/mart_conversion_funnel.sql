with sessions as (
    select anonymous_session_id,
           max((event_type = 'session_start')::int) as sessions,
           max((event_type = 'product_view')::int) as product_views,
           max((event_type = 'add_to_cart')::int) as add_to_carts,
           max((event_type = 'purchase')::int) as purchases
    from {{ ref('stg_web_events') }} group by 1
), totals as (
    select sum(sessions) as sessions, sum(product_views) as product_views,
           sum(add_to_carts) as add_to_carts, sum(purchases) as purchases from sessions
)
select *, product_views::numeric / nullif(sessions, 0) as view_rate,
       add_to_carts::numeric / nullif(product_views, 0) as cart_rate,
       purchases::numeric / nullif(sessions, 0) as purchase_rate
from totals

