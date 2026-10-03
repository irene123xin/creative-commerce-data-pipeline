select * from {{ ref('fact_orders') }} where revenue < 0

