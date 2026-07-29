SELECT 
    date_trunc('minute', timestamp) - 
    (CAST(EXTRACT(minute FROM timestamp) AS integer) % 5) * interval '1 minute' AS time_bucket,
    AVG(delay_seconds) AS avg_delay_sec,
    MAX(delay_seconds) AS max_delay_sec,
    COUNT(DISTINCT vehicle_id) AS active_trams
FROM tram_telemetry
WHERE timestamp >= NOW() - INTERVAL '3 hours'
GROUP BY 1
ORDER BY 1 ASC;