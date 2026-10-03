select
    customer_id,
    cast(signup_date as date) as signup_date,
    lower(acquisition_channel) as acquisition_channel,
    region,
    age_group,
    _batch_id,
    cast(_ingested_at as timestamptz) as ingested_at
from {{ source('raw', 'customers') }}

