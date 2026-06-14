from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.sql import func
from .base import Base


class Satellite(Base):
    __tablename__ = "satellites"

    id              = Column(Integer, primary_key=True)
    norad_id        = Column(Integer, unique=True, nullable=False)
    object_name     = Column(String(255))
    object_id       = Column(String(100))
    epoch_time      = Column(DateTime)
    inclination     = Column(Float)
    eccentricity    = Column(Float)
    mean_motion     = Column(Float)     # rev/day
    bstar           = Column(Float)
    raan            = Column(Float)     # degrees
    arg_of_perigee  = Column(Float)     # degrees
    mean_anomaly    = Column(Float)     # degrees
    rev_at_epoch    = Column(Integer)
    created_at      = Column(DateTime, server_default=func.now())
    updated_at      = Column(DateTime, server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<Satellite norad_id={self.norad_id} name={self.object_name}>"