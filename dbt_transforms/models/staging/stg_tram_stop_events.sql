with parsed as (
    select
        cast(id as int64) as event_id,
        cast(route_id as string) as route_id,
        cast(vehicle_id as string) as vehicle_id,
        cast(latitude as numeric) as latitude,
        cast(longitude as numeric) as longitude,
        cast(event_type as string) as event_type,
        cast(stop_id as string) as stop_id,
        cast(delay_seconds as int64) as delay_seconds,
        cast(timestamp as string) as raw_timestamp,
        safe_cast(timestamp as timestamp) as event_at,
        safe_cast(created_at as timestamp) as created_at
    from {{ source('raw_hsl', 'tram_stop_events') }}
),

deduplicated as (
    select
        *,
        row_number() over (
            partition by vehicle_id, stop_id, event_type, raw_timestamp
            order by created_at desc
        ) as row_num
    from parsed
)

select
    event_id,
    route_id,
    vehicle_id,
    latitude,
    longitude,
    event_type,
    stop_id,
    delay_seconds,
    event_at,
    created_at,
    case
        when delay_seconds > 120 then 'Late'
        when delay_seconds < -60 then 'Early'
        else 'On Time'
    end as punctuality_status
from deduplicated
where row_num = 1
