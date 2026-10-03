select event_id, customer_id, anonymous_session_id, event_at, event_at::date as event_date,
       event_type, product_id, campaign_id, _batch_id as batch_id
from {{ ref('stg_web_events') }}

