from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, JSON, DateTime, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    name = Column(String)
    xp = Column(Integer, default=0)
    daily_streak = Column(Integer, default=0)
    level = Column(Integer, default=1)
    level_progress = Column(Integer, default=0)

    badges = Column(JSON, default=list)
    
    progress_records = relationship("Progress", back_populates="user", cascade="all, delete-orphan")

    @property
    def completed_lessons(self):
        return list(set(str(p.lesson_id) for p in self.progress_records))

    last_practice_date = Column(DateTime(timezone=True), nullable=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class Unit(Base):
    __tablename__ = "units"

    id = Column(String, primary_key=True, index=True) # This will be like "unit_xyz"
    title = Column(String)
    description = Column(String, nullable=True)
    order = Column(Integer, default=0)
    is_published = Column(Boolean, default=False)
    
    lessons = relationship("Lesson", back_populates="unit", cascade="all, delete-orphan")

class Lesson(Base):
    __tablename__ = "lessons"

    id = Column(String, primary_key=True, index=True) # "lesson_xyz"
    unit_id = Column(String, ForeignKey("units.id", ondelete="CASCADE"))
    title = Column(String)
    description = Column(String, nullable=True)
    xp = Column(Integer, default=10)
    order = Column(Integer, default=0)
    is_published = Column(Boolean, default=False)
    achievement_id = Column(String, nullable=True) # ID of achievement to unlock upon completion
    
    unit = relationship("Unit", back_populates="lessons")
    tasks = relationship("Task", back_populates="lesson", cascade="all, delete-orphan")

class Task(Base):
    __tablename__ = "tasks"

    id = Column(String, primary_key=True, index=True) # "task_xyz"
    lesson_id = Column(String, ForeignKey("lessons.id", ondelete="CASCADE"))
    type = Column(String) # REPEAT_SIGN, etc.
    order_index = Column(Integer, default=0)
    prompt = Column(String)
    video_url = Column(String, nullable=True)
    options = Column(JSON, nullable=True)
    expected_label = Column(String, nullable=True)
    min_confidence = Column(Float, nullable=True)

    
    lesson = relationship("Lesson", back_populates="tasks")

class Achievement(Base):
    __tablename__ = "achievements"

    id = Column(String, primary_key=True, index=True)
    title = Column(String)
    description = Column(String)
    icon = Column(String)
    condition_type = Column(String, nullable=True)
    condition_value = Column(String, nullable=True)

class Progress(Base):
    __tablename__ = "progress"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"))
    lesson_id = Column(String)
    unit_id = Column(String)
    completed_at = Column(DateTime(timezone=True), server_default=func.now())
    xp_earned = Column(Integer)
    tasks_completed = Column(Integer)
    total_tasks = Column(Integer)
    mistakes = Column(Integer)
    is_perfect = Column(Boolean)

    user = relationship("User", back_populates="progress_records")
