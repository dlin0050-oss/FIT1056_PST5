"""app/teacher.py: Music School Management System module."""
from app.user import User

class TeacherUser(User):
    """Represents a teacher user in the system."""
    def __init__(self, id, name, speciality=None):
        """Initialise model attributes from saved record fields."""
        super().__init__(id, name)
        self.speciality = speciality

class Course:
    """Represents a course offered in the schedule."""
    def __init__(self, id, name, instrument, teacher_id, enrolled_student_ids=None, lessons=None):
        """Initialise model attributes from saved record fields."""
        self.id = id
        self.name = name
        self.instrument = instrument
        self.teacher_id = teacher_id
        self.enrolled_student_ids = enrolled_student_ids if enrolled_student_ids is not None else []
        self.lessons = lessons if lessons is not None else []
