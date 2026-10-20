"""Shared business logic for the cumulative PST1–5 application."""
import json
import csv
import logging
import math
from copy import deepcopy
from functools import wraps
from datetime import datetime
from pathlib import Path
from app.student import StudentUser
from app.teacher import TeacherUser, Course


def persisted_change(method):
    """Restore in-memory state if validation or saving fails."""
    @wraps(method)
    def wrapped(self, *args, **kwargs):
        """Execute one mutation with a restorable snapshot of manager state."""
        before = deepcopy(self.__dict__)
        try:
            return method(self, *args, **kwargs)
        except Exception:
            self.__dict__.clear()
            self.__dict__.update(before)
            raise
    return wrapped


class ScheduleManager:
    """Own business rules and persistent school records, separate from the GUI."""
    def __init__(self, data_path=None):
        """Initialise the manager and load saved school records."""
        self.data_path = Path(data_path) if data_path else Path(__file__).resolve().parents[1] / 'data/msms.json'
        self.students, self.teachers, self.courses, self.attendance_log = [], [], [], []
        self._load_data()

    def _load_data(self):
        """Load JSON records, restore counters and reconcile enrolment lists."""
        data = json.loads(self.data_path.read_text(encoding='utf-8')) if self.data_path.exists() else {}
        self._validate_data(data)
        self.students = [StudentUser(**s) for s in data.get('students', [])]
        self.teachers = [TeacherUser(**t) for t in data.get('teachers', [])]
        self.courses = [Course(**c) for c in data.get('courses', [])]
        self.attendance_log = data.get('attendance', [])
        self.finance_log = data.get('finance', [])
        for label in ('student', 'teacher', 'course'):
            records = getattr(self, label + 's')
            next_id = max((int(x.id) for x in records), default=0) + 1
            setattr(self, 'next_' + label + '_id', max(next_id, int(data.get('next_' + label + '_id', 1))))
        self.next_lesson_id = max((int(l['lesson_id']) for c in self.courses for l in c.lessons), default=0) + 1
        self.next_lesson_id = max(self.next_lesson_id, int(data.get('next_lesson_id', 1)))
        # Student memberships are authoritative when legacy lists disagree.
        for c in self.courses:
            c.enrolled_student_ids = [s.id for s in self.students if c.id in s.enrolled_course_ids]

    @staticmethod
    def _validate_data(data):
        """Reject malformed stored structures before creating model objects."""
        if not isinstance(data, dict):
            raise ValueError('Data file must contain a JSON object.')
        required = {'students': ('id', 'name'), 'teachers': ('id', 'name', 'speciality'),
                    'courses': ('id', 'name', 'instrument', 'teacher_id'),
                    'attendance': ('student_id', 'course_id', 'timestamp'),
                    'finance': ('student_id', 'amount', 'method', 'timestamp')}
        for kind, fields in required.items():
            records = data.get(kind, [])
            if not isinstance(records, list):
                raise ValueError(f'{kind} must be a list.')
            for row in records:
                if not isinstance(row, dict) or any(f not in row for f in fields):
                    raise ValueError(f'Invalid record in {kind}.')
        for kind in ('students', 'teachers', 'courses'):
            ids = [row['id'] for row in data.get(kind, [])]
            if any(type(i) is not int or i < 1 for i in ids) or len(set(ids)) != len(ids):
                raise ValueError(f'{kind} IDs must be unique positive integers.')
            if any(not isinstance(row['name'], str) for row in data.get(kind, [])):
                raise ValueError(f'{kind} names must be text.')
        for row in data.get('students', []):
            if not isinstance(row.get('enrolled_course_ids', []), list):
                raise ValueError('Student enrolments must be a list.')
        for row in data.get('courses', []):
            if not isinstance(row.get('lessons', []), list):
                raise ValueError('Course lessons must be a list.')
            for lesson in row.get('lessons', []):
                if not isinstance(lesson, dict) or any(k not in lesson for k in ('lesson_id', 'day', 'start_time', 'room')):
                    raise ValueError('Invalid lesson record.')

    def _save_data(self):
        """Atomically replace the JSON file after serialising all records."""
        data = {name: [x.__dict__ for x in getattr(self, name)] for name in ('students', 'teachers', 'courses')}
        data['attendance'] = self.attendance_log
        data['finance'] = self.finance_log
        data['next_lesson_id'] = self.next_lesson_id
        for label in ('student', 'teacher', 'course'):
            data['next_' + label + '_id'] = getattr(self, 'next_' + label + '_id')
        self.data_path.parent.mkdir(parents=True, exist_ok=True)
        temp = self.data_path.with_suffix('.tmp')
        temp.write_text(json.dumps(data, indent=4), encoding='utf-8')
        temp.replace(self.data_path)

    @staticmethod
    def _text(value, field):
        """Trim required text and reject blank input."""
        if not isinstance(value, str):
            raise ValueError(f'{field} must be text.')
        value = value.strip()
        if not value:
            raise ValueError(f'{field} cannot be blank.')
        return value

    def _find(self, records, record_id, label):
        """Find a record by ID or raise a user-facing validation error."""
        result = next((x for x in records if str(x.id) == str(record_id)), None)
        if result is None:
            raise ValueError(f'{label} not found.')
        return result

    def find_student_by_id(self, student_id):
        """Return a matching student, or None when the ID is unknown."""
        return next((s for s in self.students if str(s.id) == str(student_id)), None)

    def find_course_by_id(self, course_id):
        """Return a matching course, or None when the ID is unknown."""
        return next((c for c in self.courses if str(c.id) == str(course_id)), None)

    def find_students(self, term):
        """Find students by case-insensitive partial name."""
        return [s for s in self.students if term.strip().casefold() in s.name.casefold()]

    def find_teachers(self, term):
        """Find teachers by partial name or instrument speciality."""
        term = term.strip().casefold()
        return [t for t in self.teachers if term in t.name.casefold() or term in (t.speciality or '').casefold()]

    @persisted_change
    def add_student(self, name):
        """Create an unenrolled student with a persistent automatic ID."""
        student = StudentUser(self.next_student_id, self._text(name, 'Name'))
        self.students.append(student)
        self.next_student_id += 1
        self._save_data()
        return student

    @persisted_change
    def add_teacher(self, name, speciality):
        """Create a teacher with validated text and a persistent automatic ID."""
        teacher = TeacherUser(self.next_teacher_id, self._text(name, 'Name'), self._text(speciality, 'Speciality'))
        self.teachers.append(teacher)
        self.next_teacher_id += 1
        self._save_data()
        return teacher

    @persisted_change
    def add_course(self, name, instrument, teacher_id):
        """Create a course with a teacher whose speciality matches."""
        name, instrument = self._text(name, 'Name'), self._text(instrument, 'Instrument')
        teacher = self._find(self.teachers, teacher_id, 'Teacher')
        if (teacher.speciality or '').casefold() != instrument.casefold():
            raise ValueError('The teacher speciality must match the instrument.')
        course = Course(self.next_course_id, name, instrument, teacher.id)
        self.courses.append(course)
        self.next_course_id += 1
        self._save_data()
        return course

    @persisted_change
    def register_new_student(self, name, instrument):
        """Register a student and enrol them in the first matching course."""
        name, instrument = self._text(name, 'Name'), self._text(instrument, 'Instrument')
        course = next((c for c in self.courses if c.instrument.casefold() == instrument.casefold()), None)
        if course is None:
            raise ValueError('No course is available for this instrument. Add a teacher and course first.')
        self._find(self.teachers, course.teacher_id, 'Course teacher')
        student = StudentUser(self.next_student_id, name, [course.id])
        self.students.append(student)
        course.enrolled_student_ids.append(student.id)
        self.next_student_id += 1
        self._save_data()
        logging.info('Registered student ID %s for %s', student.id, course.name)
        return student

    @persisted_change
    def enrol_student(self, student_id, course_id):
        """Add an enrolment to both the student and course memberships."""
        student = self._find(self.students, student_id, 'Student')
        course = self._find(self.courses, course_id, 'Course')
        if course.id in student.enrolled_course_ids:
            raise ValueError('Student is already enrolled in this course.')
        student.enrolled_course_ids.append(course.id)
        course.enrolled_student_ids.append(student.id)
        self._save_data()

    @persisted_change
    def switch_course(self, student_id, from_course_id, to_course_id):
        """Transfer an enrolment and update both sides before saving."""
        student = self._find(self.students, student_id, 'Student')
        old = self._find(self.courses, from_course_id, 'Original course')
        new = self._find(self.courses, to_course_id, 'New course')
        if old.id not in student.enrolled_course_ids:
            raise ValueError('Student is not enrolled in the original course.')
        if new.id in student.enrolled_course_ids:
            raise ValueError('Student is already enrolled in the destination course.')
        student.enrolled_course_ids.remove(old.id)
        student.enrolled_course_ids.append(new.id)
        old.enrolled_student_ids = [i for i in old.enrolled_student_ids if i != student.id]
        new.enrolled_student_ids.append(student.id)
        self._save_data()
        return True

    @persisted_change
    def update_student(self, student_id, name):
        """Validate and persist a student name change."""
        student = self._find(self.students, student_id, 'Student')
        student.name = self._text(name, 'Name')
        self._save_data()

    @persisted_change
    def update_teacher(self, teacher_id, name, speciality):
        """Update a teacher while preserving compatibility with assigned courses."""
        teacher = self._find(self.teachers, teacher_id, 'Teacher')
        name, speciality = self._text(name, 'Name'), self._text(speciality, 'Speciality')
        if any(c.teacher_id == teacher.id and c.instrument.casefold() != speciality.casefold() for c in self.courses):
            raise ValueError('Speciality must remain compatible with assigned courses.')
        teacher.name, teacher.speciality = name, speciality
        self._save_data()

    @persisted_change
    def remove_student(self, student_id):
        """Remove current enrolments while retaining historical records."""
        student = self._find(self.students, student_id, 'Student')
        self.students.remove(student)
        for c in self.courses:
            c.enrolled_student_ids = [i for i in c.enrolled_student_ids if i != student.id]
        self._save_data()

    @persisted_change
    def remove_teacher(self, teacher_id):
        """Remove an unassigned teacher, rejecting teachers with courses."""
        teacher = self._find(self.teachers, teacher_id, 'Teacher')
        if any(c.teacher_id == teacher.id for c in self.courses):
            raise ValueError('Cannot remove a teacher assigned to a course.')
        self.teachers.remove(teacher)
        self._save_data()

    @persisted_change
    def check_in(self, student_id, course_id, day=None):
        """Validate enrolment and optional weekday, then save timestamped attendance."""
        student = self._find(self.students, student_id, 'Student')
        course = self._find(self.courses, course_id, 'Course')
        if course.id not in student.enrolled_course_ids:
            raise ValueError('Student is not enrolled in this course.')
        if day is not None and course not in self.courses_on_day(day):
            raise ValueError('This course does not run on the selected day.')
        self.attendance_log.append({'student_id': student.id, 'course_id': course.id, 'timestamp': datetime.now().isoformat()})
        self._save_data()
        return True

    def student_card(self, student_id):
        """Build a plain-text student badge for download."""
        student = self._find(self.students, student_id, 'Student')
        names = [c.name for c in self.courses if c.id in student.enrolled_course_ids]
        return f'MUSIC SCHOOL ID BADGE\nID: {student.id}\nName: {student.name}\nEnrolled in: {", ".join(names) or "None"}\n'

    @persisted_change
    def add_lesson(self, course_id, day, start_time, room):
        """Schedule a weekday lesson, rejecting identical room or teacher start times."""
        course = self._find(self.courses, course_id, 'Course')
        room = self._text(room, 'Room')
        if day not in ('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'):
            raise ValueError('Choose a weekday.')
        datetime.strptime(start_time, '%H:%M')
        for c in self.courses:
            for lesson in c.lessons:
                if lesson['day'] == day and lesson['start_time'] == start_time and (lesson['room'].casefold() == room.casefold() or c.teacher_id == course.teacher_id):
                    raise ValueError('Room or teacher is already booked at this start time.')
        course.lessons.append({'lesson_id': self.next_lesson_id, 'day': day, 'start_time': start_time, 'room': room})
        self.next_lesson_id += 1
        self._save_data()

    def daily_roster(self, day):
        """Return every lesson on a weekday, ordered by start time."""
        rows = []
        for course in self.courses:
            teacher = next((t for t in self.teachers if t.id == course.teacher_id), None)
            for lesson in course.lessons:
                if lesson['day'] == day:
                    rows.append({'Course ID': course.id, 'Course': course.name, 'Time': lesson['start_time'], 'Room': lesson['room'], 'Teacher': teacher.name if teacher else 'Unknown'})
        return sorted(rows, key=lambda row: row['Time'])

    def courses_on_day(self, day):
        """Return active courses with at least one lesson on this weekday."""
        return [c for c in self.courses if any(l['day'] == day for l in c.lessons)]

    def students_on_day(self, day):
        """Return students enrolled in any course scheduled for this weekday."""
        ids = {c.id for c in self.courses_on_day(day)}
        return [s for s in self.students if ids.intersection(s.enrolled_course_ids)]

    def student_courses_on_day(self, student_id, day):
        """Restrict course choices to this student's enrolments on the chosen day."""
        student = self._find(self.students, student_id, 'Student')
        return [c for c in self.courses_on_day(day) if c.id in student.enrolled_course_ids]

    @persisted_change
    def record_payment(self, student_id, amount, method):
        """Validate and save a positive payment for an existing student."""
        student = self._find(self.students, student_id, 'Student')
        try:
            amount = float(amount)
        except (TypeError, ValueError):
            raise ValueError('Payment amount must be a number.') from None
        if not math.isfinite(amount) or amount <= 0:
            raise ValueError('Payment amount must be positive and finite.')
        amount = round(amount, 2)
        if amount < 0.01:
            raise ValueError('Payment amount must be at least 0.01.')
        method = self._text(method, 'Payment method')
        record = {'student_id': student.id, 'amount': amount, 'method': method,
                  'timestamp': datetime.now().isoformat()}
        self.finance_log.append(record)
        self._save_data()
        logging.info('Payment %.2f recorded for student ID %s', amount, student.id)
        return record

    def get_payment_history(self, student_id):
        """Return copies of this student's payments; historical IDs remain searchable."""
        return [dict(p) for p in self.finance_log if str(p['student_id']) == str(student_id)]

    def export_report(self, kind, out_path):
        """Write a finance or attendance CSV, including headers for an empty log."""
        if kind == 'finance':
            records, headers = self.finance_log, ['student_id', 'amount', 'method', 'timestamp']
        elif kind == 'attendance':
            records, headers = self.attendance_log, ['student_id', 'course_id', 'timestamp']
        else:
            raise ValueError('Unknown report type. Choose finance or attendance.')
        out_path = Path(out_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with out_path.open('w', newline='', encoding='utf-8') as stream:
            writer = csv.DictWriter(stream, fieldnames=headers)
            writer.writeheader()
            writer.writerows(records)
        logging.info('Exported %s report', kind)
        return out_path

    @persisted_change
    def cancel_lesson(self, lesson_id, reason):
        """Remove a scheduled lesson and log its cancellation reason."""
        reason = self._text(reason, 'Cancellation reason')
        for course in self.courses:
            lesson = next((l for l in course.lessons if str(l['lesson_id']) == str(lesson_id)), None)
            if lesson is not None:
                course.lessons.remove(lesson)
                self._save_data()
                logging.warning('Lesson ID %s cancelled: %s', lesson_id, reason)
                return True
        raise ValueError('Lesson not found.')

    def create_course(self, name, instrument, teacher_id):
        """Provide the template's method name while retaining the PST4 API."""
        return self.add_course(name, instrument, teacher_id)
