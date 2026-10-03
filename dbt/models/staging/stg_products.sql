select product_id, product_name, category,
       cast(price as numeric(12,2)) as price,
       cast(cost as numeric(12,2)) as cost,
       cast(price as numeric(12,2)) - cast(cost as numeric(12,2)) as unit_margin,
       _batch_id
from {{ source('raw', 'products') }}

