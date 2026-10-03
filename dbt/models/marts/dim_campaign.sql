select campaign_id, campaign_name, channel, start_date, end_date
from {{ ref('stg_campaigns') }}
union all
select 'DIRECT_OR_UNKNOWN', 'Direct or unknown', 'direct_or_unknown', null::date, null::date
