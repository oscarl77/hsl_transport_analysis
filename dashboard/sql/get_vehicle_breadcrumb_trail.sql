SELECT 
    latitude, 
    longitude, 
    speed, 
    delay_seconds, 
    timestamp
FROM tram_telemetry
WHERE vehicle_id = :vehicle_id
  AND timestamp >= NOW() - INTERVAL '30 minutes'
ORDER BY timestamp ASC;