WITH latest_vehicle_positions AS (
    SELECT DISTINCT ON (vehicle_id) 
        route_id, 
        vehicle_id, 
        delay_seconds
    FROM tram_telemetry
    WHERE timestamp >= (SELECT MAX(timestamp) FROM tram_telemetry) - INTERVAL '5 minutes'
    ORDER BY vehicle_id, timestamp DESC
)

SELECT 
    route_id,
    COUNT(DISTINCT vehicle_id) AS active_vehicles,
    ROUND(AVG(delay_seconds)) AS avg_delay_sec,
    MAX(delay_seconds) AS max_delay_sec
FROM latest_vehicle_positions
GROUP BY route_id
ORDER BY avg_delay_sec DESC;