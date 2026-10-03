select order_item_id, order_id, product_id, cast(quantity as integer) as quantity,
       cast(unit_price as numeric(12,2)) as unit_price,
       cast(unit_cost as numeric(12,2)) as unit_cost,
       cast(quantity as integer) * cast(unit_price as numeric(12,2)) as gross_revenue,
       cast(quantity as integer) * (cast(unit_price as numeric(12,2)) - cast(unit_cost as numeric(12,2))) as gross_margin,
       _batch_id
from {{ source('raw', 'order_items') }}

