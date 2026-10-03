select * from {{ ref('mart_customer_ltv') }}
where observed_lifetime_revenue < 0
