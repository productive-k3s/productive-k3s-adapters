# Docker Compose adapter

The first adapter reads an already-built Compose definition. Services using `build:` without an `image:` are rejected intentionally: image building belongs to OpenShip or another upstream producer.
