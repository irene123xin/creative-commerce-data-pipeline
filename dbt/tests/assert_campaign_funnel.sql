select * from {{ ref('stg_campaigns') }}
where clicks > impressions or reported_conversions > clicks
