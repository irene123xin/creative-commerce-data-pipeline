select customer_id, signup_date, acquisition_channel, region, age_group
from {{ ref('stg_customers') }}

