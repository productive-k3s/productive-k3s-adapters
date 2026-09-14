# Adapter Docker Compose

El primer adapter lee una definicion Compose ya construida. Si un servicio usa `build:` sin `image:`, se rechaza: construir imagenes corresponde a OpenShip u otra herramienta anterior en el pipeline.
