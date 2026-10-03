select event_id, nullif(customer_id, '') as customer_id, anonymous_session_id,
       cast(timestamp as timestamptz) as event_at, event_type,
       nullif(product_id, '') as product_id, nullif(campaign_id, '') as campaign_id, _batch_id
from {{ source('raw', 'website_events') }}

