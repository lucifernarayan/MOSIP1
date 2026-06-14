from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from .base import Base


class OrbitalParameter(Base):
    __tablename__ = "orbital_parameters"

    id              = Column(Integer, primary_key=True)
    satellite_id    = Column(Integer, ForeignKey("satellites.id", ondelete="CASCADE"), nullable=False)
    epoch_time      = Column(DateTime)
    inclination     = Column(Float)         # degrees
    eccentricity    = Column(Float)
    mean_motion     = Column(Float)         # rev/day
    altitude_km     = Column(Float)         # mean circular altitude (km)
    apogee_km       = Column(Float)         # apogee altitude (km)
    perigee_km      = Column(Float)         # perigee altitude (km)
    semi_major_axis = Column(Float)         # km
    raan            = Column(Float)         # degrees
    arg_of_perigee  = Column(Float)         # degrees
    period_minutes  = Column(Float)         # orbital period (min)
    orbit_type      = Column(String(10))    # LEO / MEO / GEO / HEO / VLEO
    created_at      = Column(DateTime, server_default=func.now())

    def __repr__(self):
        return (
            f"<OrbitalParameter sat_id={self.satellite_id} "
            f"alt={self.altitude_km:.0f}km orbit={self.orbit_type}>"
        )