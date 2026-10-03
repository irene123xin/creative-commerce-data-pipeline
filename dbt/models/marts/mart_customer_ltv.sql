select *, completed_orders > 1 as is_repeat_customer,
       rank() over (partition by acquisition_channel order by observed_lifetime_revenue desc) as channel_value_rank
from {{ ref('int_customer_lifetime_value') }}
