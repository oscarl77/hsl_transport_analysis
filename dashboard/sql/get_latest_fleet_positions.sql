SELECT DISTINCT ON (vehicle_id)
    route_id,
    vehicle_id,
    latitude,
    longitude,
    delay_seconds,
    speed,
    timestamp
FROM tram_telemetry
WHERE timestamp >= (SELECT MAX(timestamp) FROM tram_telemetry) - INTERVAL '3 minute'
ORDER BY vehicle_id, timestamp DESC;