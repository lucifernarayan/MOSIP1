from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from .base import Base


class RiskAssessment(Base):
    __tablename__ = "risk_assessments"

    id              = Column(Integer, primary_key=True)
    satellite_id    = Column(Integer, ForeignKey("satellites.id", ondelete="CASCADE"), nullable=False)
    risk_score      = Column(Float)         # overall 0–100
    risk_level      = Column(String(20))    # LOW / MEDIUM / HIGH / CRITICAL
    collision_risk  = Column(Float)         # collision component 0–100
    debris_risk     = Column(Float)         # debris density component 0–100
    altitude_risk   = Column(Float)         # altitude-based component 0–100
    orbit_type      = Column(String(10))
    risk_drivers    = Column(Text)          # JSON-serialized list of strings
    assessed_at     = Column(DateTime, server_default=func.now())

    def __repr__(self):
        return (
            f"<RiskAssessment sat_id={self.satellite_id} "
            f"score={self.risk_score} level={self.risk_level}>"
        )