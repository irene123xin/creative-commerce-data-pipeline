select order_id, customer_id, cast(order_date as timestamptz) as order_at,
       status, cast(discount as numeric(12,2)) as discount,
       cast(revenue as numeric(12,2)) as revenue,
       nullif(campaign_id, '') as campaign_id, _batch_id,
       cast(_ingested_at as timestamptz) as ingested_at
from {{ source('raw', 'orders') }}

