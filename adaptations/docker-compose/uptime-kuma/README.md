# Docker Compose Uptime Kuma adaptation

This adaptation validates the baseline `docker-compose` producer using the
upstream Uptime Kuma Compose shape.

Source:

- `https://github.com/louislam/uptime-kuma/blob/master/compose.yaml`

Included:

- Uptime Kuma web application on port `3001`

Known review item:

- The upstream Compose file uses `./data:/app/data`. The current generic
  resolver records this as a volume review item but does not yet generate a
  Productive K3S persistence mapping. This adaptation is therefore a liveness
  validator, not a production persistence example.
