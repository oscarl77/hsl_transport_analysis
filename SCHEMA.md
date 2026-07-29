Table 1: tram_telemetry

Continuous vehicle position and tracking updates extracted from HFP `VP` events.

| column | definition |
| :--- | :--- |
| **id** | Auto-incrementing surrogate primary key |
| **route_id** | Line or route display identifier (parsed from `desi`) |
| **vehicle_id** | Unique vehicle identification number (parsed from `veh`) |
| **latitude** | WGS84 latitude coordinate (parsed from `lat`) |
| **longitude** | WGS84 longitude coordinate (parsed from `lon`) |
| **delay_seconds** | Schedule offset in seconds; positive is late, negative is early (parsed from `dl`) |
| **speed** | Vehicle velocity in meters per second (parsed from `spd`) |
| **heading** | Compass bearing in degrees from 0 to 360 (parsed from `hdg`) |
| **timestamp** | UTC epoch timestamp in seconds recorded by the vehicle (parsed from `tsi`) |
| **created_at** | Database insertion timestamp defaults to current execution time |


Table 2: tram_stop_events 

Discrete transit stop milestones extracted from HFP `ARR`, `DEP`, and `PAS` events.

| column | definition |
| :--- | :--- |
| **id** | Auto-incrementing surrogate primary key |
| **route_id** | Line or route display identifier (parsed from `desi`) |
| **vehicle_id** | Unique vehicle identification number (parsed from `veh`) |
| **event_type** | Type of stop milestone recorded: `arr` (arrival), `dep` (departure), or `pas` (pass-through) |
| **stop_id** | Unique HSL stop identifier (parsed from `stop`) |
| **delay_seconds** | Schedule offset at the stop in seconds (parsed from `dl`) |
| **timestamp** | UTC epoch timestamp in seconds recorded by the vehicle (parsed from `tsi`) |
| **created_at** | Database insertion timestamp defaults to current execution time |