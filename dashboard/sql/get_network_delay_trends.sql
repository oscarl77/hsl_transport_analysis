SELECT 
    date_trunc('hour', timestamp::timestamp) + 
    (MOD(EXTRACT(minute FROM timestamp::timestamp)::integer, 5) * INTERVAL '1 minute') AS time_bucket,
    AVG(delay_seconds) AS avg_delay_sec,
    MAX(delay_seconds) AS max_delay_sec,
    COUNT(DISTINCT vehicle_id) AS active_trams
FROM tram_telemetry
WHERE timestamp::timestamp >= NOW() - INTERVAL '3 hours'
GROUP BY 1
ORDER BY 1 ASC;