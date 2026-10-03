select d::date as date_day,
       extract(year from d)::int as year,
       extract(month from d)::int as month,
       extract(week from d)::int as week,
       to_char(d, 'YYYY-MM') as year_month
from generate_series('2025-01-01'::date, '2027-12-31'::date, interval '1 day') d

