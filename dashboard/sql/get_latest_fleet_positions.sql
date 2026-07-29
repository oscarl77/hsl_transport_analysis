SELECT DISTINCT ON (vehicle_id)
    route_id,
    vehicle_id,
    latitude,
    longitude,
    delay_seconds,
    speed,
    timestamp
FROM tram_telemetry
ORDER BY vehicle_id, timestamp DESC;