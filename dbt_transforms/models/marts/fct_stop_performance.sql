with staging as (
    select * from {{ ref('stg_tram_stop_events') }}
)

select
    date(event_at) as performance_date,
    route_id,
    stop_id,
    count(distinct vehicle_id) as active_vehicles_count,
    countif(event_type = 'arr') as total_arrivals,
    countif(event_type = 'dep') as total_departures,
    round(avg(delay_seconds), 2) as avg_delay_seconds,
    max(delay_seconds) as max_delay_seconds,
    countif(punctuality_status = 'Late') as late_count,
    countif(punctuality_status = 'Early') as early_count,
    countif(punctuality_status = 'On Time') as on_time_count,
    round(safe_divide(countif(punctuality_status = "On Time"), count(*)) * 100, 2) as on_time_rate_pct
from staging
group by 1, 2, 3
