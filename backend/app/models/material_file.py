
from sqlalchemy import Column, Integer, String, ForeignKey
from datetime import datetime
from ..database import Base

class MaterialFile(Base):
    __tablename__ = "material_files"

    id = Column(Integer, primary_key=True, index=True)
    material_id = Column(Integer, ForeignKey("materials.id", ondelete="CASCADE"), nullable=False)
    file_url = Column(String, nullable=False)
    filename = Column(String, nullable=False)
    uploaded_at = Column(String, default=lambda: datetime.utcnow().isoformat())
