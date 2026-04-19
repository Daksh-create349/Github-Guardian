from sqlalchemy import Column, Integer, String, DateTime, Text
from datetime import datetime
from src.db.session import Base

class PushHistory(Base):
    __tablename__ = "push_history"

    id = Column(Integer, primary_key=True, index=True)
    github_username = Column(String, index=True, nullable=False)
    repository_name = Column(String, index=True, nullable=False)
    branch_name = Column(String, nullable=False)
    commit_message = Column(Text, nullable=True)
    status = Column(String, nullable=False) # e.g. success, new_repo, auto_merged, conflict_resolved, error
    log_details = Column(Text, nullable=True) # Optional JSON or text block with details
    created_at = Column(DateTime, default=datetime.utcnow)
