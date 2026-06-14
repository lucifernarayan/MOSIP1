from backend.repositories.satellite_repository import (
    SatelliteRepository
)

repo = SatelliteRepository()

print(
    "Satellite Count:",
    repo.get_count()
)