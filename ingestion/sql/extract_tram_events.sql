select
    id,
    route_id,
    vehicle_id,
    latitude,
    longitude,
    event_type,
    stop_id,
    delay_seconds,
    timestamp,
    created_at
from tram_stop_events
where created_at > %s
  and created_at <= %s
order by created_at asc;