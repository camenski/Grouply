# from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
# from sqlalchemy.sql import func
# from app.db.base_class import Base

# class GroupInvite(Base):
#     __tablename__ = "group_invites"
#     id = Column(Integer, primary_key=True, index=True)
#     group_id = Column(Integer, ForeignKey("groups.id", ondelete="CASCADE"), nullable=False)
#     token = Column(String(128), unique=True, index=True, nullable=False)
#     created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
#     expires_at = Column(DateTime(timezone=True), nullable=True)
#     max_uses = Column(Integer, nullable=True)   # None = unlimited
#     uses = Column(Integer, default=0, nullable=False)
#     is_active = Column(Boolean, default=True, nullable=False)
