select campaign_id, campaign_name, lower(channel) as channel,
       cast(spend as numeric(14,2)) as spend, cast(impressions as bigint) as impressions,
       cast(clicks as bigint) as clicks, cast(conversions as bigint) as reported_conversions,
       cast(start_date as date) as start_date, cast(end_date as date) as end_date, _batch_id
from {{ source('raw', 'campaigns') }}

