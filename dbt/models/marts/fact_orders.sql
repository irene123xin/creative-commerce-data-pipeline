select order_id, customer_id, campaign_id, order_at, order_at::date as order_date,
       status, discount, revenue, _batch_id as batch_id
from {{ ref('stg_orders') }}

