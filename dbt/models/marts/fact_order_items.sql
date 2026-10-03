select order_item_id, order_id, product_id, quantity, unit_price, unit_cost,
       gross_revenue, gross_margin, _batch_id as batch_id
from {{ ref('stg_order_items') }}

