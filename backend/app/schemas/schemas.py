from pydantic import BaseModel, Field, ConfigDict, AliasChoices
from typing import List, Optional, Union, Any
from enum import Enum

def to_camel(string: str) -> str:
    words = string.split('_')
    return words[0] + ''.join(word.capitalize() for word in words[1:])

class CamelModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, from_attributes=True)

# --- Enums ---
class TaskType(str, Enum):
    RepeatSign = 'REPEAT_SIGN'
    TextToSign = 'TEXT_TO_SIGN'
    SignToText = 'SIGN_TO_TEXT'
    VideoMultipleChoice = 'VIDEO_MULTIPLE_CHOICE'

# --- Shared Models ---
class TaskOption(CamelModel):
    id: str
    text: Optional[str] = Field(None, validation_alias=AliasChoices('text', 'labelText'))
    video_url: Optional[str] = None
    is_correct: bool

class Task(CamelModel):
    id: str
    type: TaskType
    prompt: str
    video_url: Optional[str] = None
    options: Optional[List[TaskOption]] = None

    expected_label: Optional[str] = None
    min_confidence: Optional[float] = None

class Achievement(CamelModel):
    id: str
    title: str
    description: str
    icon: str
    condition_type: Optional[str] = None
    condition_value: Optional[str] = None

# --- User Schemas ---
class UserBase(CamelModel):
    email: str

class UserCreate(UserBase):
    name: str = Field(alias="displayName")
    password: str

class UserLogin(UserBase):
    password: str

class User(CamelModel):
    id: str
    name: str = Field(alias="displayName")
    email: str
    xp: int
    daily_streak: int
    level: int
    level_progress: int
    badges: List[str]
    completed_lessons: List[str]
    last_practice_date: Optional[Any] = None
    is_admin: bool = False

class UserUpdate(CamelModel):
    name: Optional[str] = None

# --- Lesson Schemas ---
class Lesson(CamelModel):
    id: str
    title: str
    xp: int
    tasks: List[Task]

class Unit(CamelModel):
    id: str
    title: str
    lessons: List[Lesson]

# --- API Responses ---
class AuthResponse(CamelModel):
    success: bool
    message: str
    data: User

class UserResponseData(CamelModel):
    user: User

class UserResponse(CamelModel):
    success: bool
    data: UserResponseData
    message: Optional[str] = None

class CompleteLessonRequest(CamelModel):
    lesson_id: str
    unit_id: str
    xp_earned: int
    tasks_completed: int
    total_tasks: int
    mistakes: int
    # Prototype: treat this as optional and default to [] to avoid 422s when the
    # frontend doesn't send it.
    previous_badges: List[str] = Field(default_factory=list)

class CompleteLessonResponseData(CamelModel):
    user: User
    new_badges: List[str]

class CompleteLessonResponse(CamelModel):
    success: bool
    message: str
    data: CompleteLessonResponseData

class LearningPathResponseData(CamelModel):
    learning_path: List[Unit]

class LearningPathResponse(CamelModel):
    success: bool
    data: LearningPathResponseData

class LessonResponseData(CamelModel):
    lesson: Lesson
    unit: dict # Simplified unit info

class LessonResponse(CamelModel):
    success: bool
    data: LessonResponseData

class AchievementsResponseData(CamelModel):
    achievements: List[Achievement]

class AchievementsResponse(CamelModel):
    success: bool
    data: AchievementsResponseData

class ProgressItem(CamelModel):
    id: str = Field(alias="_id") # Auto-generated ID
    user_id: str
    lesson_id: str
    unit_id: str
    completed_at: str
    xp_earned: int
    tasks_completed: int
    total_tasks: int
    mistakes: int
    is_perfect: bool

class ProgressResponseData(CamelModel):
    progress: List[ProgressItem]

class ProgressResponse(CamelModel):
    success: bool
    data: ProgressResponseData

class LeaderboardEntry(CamelModel):
    user_id: str
    name: str
    xp: int
    level: int

class LeaderboardResponseData(CamelModel):
    leaderboard: List[LeaderboardEntry]

class LeaderboardResponse(CamelModel):
    success: bool
    data: LeaderboardResponseData


# --- Admin Schemas ---

class AdminUnitCreate(CamelModel):
    title: str
    description: Optional[str] = None
    order_index: int = 0
    is_published: bool = True

class AdminUnitUpdate(AdminUnitCreate):
    pass

class AdminLessonCreate(CamelModel):
    unit_id: str
    title: str
    description: Optional[str] = None
    order_index: int = 0
    xp_reward: int = 20
    is_published: bool = True
    achievement_id: Optional[str] = None

class AdminLessonUpdate(AdminLessonCreate):
    unit_id: Optional[str] = None

class AdminTaskCreate(CamelModel):
    lesson_id: str
    type: str
    prompt_text: str
    order_index: int = 0
    options: Optional[Any] = None

    sign_video_url: Optional[str] = None
    # Camera task evaluation (used by TextToSign/RepeatSign in the frontend).
    expected_label: Optional[str] = None
    min_confidence: Optional[float] = None

class AdminTaskUpdate(AdminTaskCreate):
    lesson_id: Optional[str] = None

class AdminAchievementCreate(CamelModel):
    title: str
    description: str
    icon: str
    condition_type: str = "manual"
    condition_value: Optional[str] = None

class AdminAchievementUpdate(AdminAchievementCreate):
    pass

class ReorderItem(BaseModel):
    id: str
    orderIndex: int


class ReorderRequest(CamelModel):
    items: List[ReorderItem]


class SmartReorderRequest(CamelModel):
    type: str
    id: str
    new_index: int
    parent_id: Optional[str] = None


class AdminTaskResponse(CamelModel):
    id: str
    task_id: str = Field(validation_alias="id")
    lesson_id: str
    type: str # TaskType enum? Or just str.
    prompt_text: str = Field(validation_alias="prompt")
    order_index: int
    options: Optional[Any] = None
    sign_video_url: Optional[str] = Field(None, validation_alias="video_url")

    expected_label: Optional[str] = None
    min_confidence: Optional[float] = None

class AdminLessonResponse(CamelModel):
    id: str
    lesson_id: str = Field(validation_alias="id")
    unit_id: str
    title: str
    description: Optional[str] = None
    order_index: int = Field(validation_alias="order")
    xp_reward_base: int = Field(validation_alias="xp")
    is_published: bool
    achievement_id: Optional[str] = None
    tasks: List[AdminTaskResponse]

class AdminUnitResponse(CamelModel):
    id: str
    unit_id: str = Field(validation_alias="id")
    title: str
    description: Optional[str] = None
    order_index: int = Field(validation_alias="order")
    is_published: bool
    lessons: List[AdminLessonResponse]

class AdminContentResponse(CamelModel):
    success: bool
    data: List[AdminUnitResponse]


class AdminAchievementsResponse(CamelModel):
    success: bool
    data: List[Achievement]

