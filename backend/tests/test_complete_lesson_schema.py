from backend.app.schemas.schemas import CompleteLessonRequest


def test_complete_lesson_previous_badges_default_empty():
    req = CompleteLessonRequest(
        lessonId="lesson_1",
        unitId="unit_1",
        xpEarned=10,
        tasksCompleted=3,
        totalTasks=3,
        mistakes=0,
    )
    assert req.previous_badges == []

