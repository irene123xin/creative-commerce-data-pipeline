select product_id, product_name, category, price, cost, unit_margin
from {{ ref('stg_products') }}

