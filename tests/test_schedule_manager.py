"""PST5 Arrange/Act/Assert tests using isolated pytest temporary files."""
import csv
import logging
from copy import deepcopy
import pytest
from app.schedule import ScheduleManager
from app.admin_utils import backup_data, init_logger


@pytest.fixture
def fresh_manager(tmp_path):
    """Use a unique data file per test, leaving real school data untouched."""
    return ScheduleManager(tmp_path / 'msms.json')


@pytest.fixture
def school(fresh_manager):
    """Arrange a teacher, course, two lessons and a registered student."""
    m = fresh_manager
    teacher = m.add_teacher('Teacher', 'Piano')
    course = m.create_course('Beginner Piano', 'Piano', teacher.id)
    m.add_lesson(course.id, 'Monday', '10:00', 'A')
    m.add_lesson(course.id, 'Tuesday', '10:00', 'A')
    student = m.register_new_student('Alice', 'Piano')
    return m, student, course


def test_create_course(fresh_manager):
    """A course can reference a teacher created in the same isolated test."""
    teacher = fresh_manager.add_teacher('Keys', 'Piano')  # Arrange
    course = fresh_manager.create_course('Beginner Piano', 'Piano', teacher.id)  # Act
    assert fresh_manager.courses == [course]  # Assert
    assert course.name == 'Beginner Piano'


def test_record_payment_and_history(school):
    """Saved payment history survives reloading and string ID input."""
    m, student, _ = school
    m.record_payment(str(student.id), 100, 'Credit Card')
    history = ScheduleManager(m.data_path).get_payment_history(student.id)
    assert len(history) == 1
    assert history[0]['amount'] == 100
    assert history[0]['method'] == 'Credit Card'
    assert history[0]['timestamp']


def test_get_payment_history_no_results(school):
    """An existing student with no payments has an empty history."""
    m, student, _ = school
    assert m.get_payment_history(student.id) == []


@pytest.mark.parametrize('amount', [0, -1, 'bad', None, float('nan'), float('inf'), 0.001])
def test_invalid_payment_amount(school, amount):
    """Reject non-positive, non-numeric and non-finite values without saving."""
    m, student, _ = school
    before = m.data_path.read_bytes()
    with pytest.raises(ValueError):
        m.record_payment(student.id, amount, 'Cash')
    assert m.finance_log == []
    assert m.data_path.read_bytes() == before


def test_payment_missing_student(school):
    """An unknown student cannot receive a payment record."""
    m, _, _ = school
    with pytest.raises(ValueError):
        m.record_payment(999, 10, 'Cash')
    assert not m.finance_log


def test_payment_blank_method(school):
    """A payment needs a meaningful method."""
    m, student, _ = school
    with pytest.raises(ValueError):
        m.record_payment(student.id, 10, '   ')
    assert not m.finance_log


@pytest.mark.parametrize('kind', ['finance', 'attendance'])
def test_export_report(school, tmp_path, kind):
    """CSV exports include the appropriate headers and recorded transaction."""
    m, student, course = school
    m.record_payment(student.id, 12.5, 'Cash')
    m.check_in(student.id, course.id, 'Monday')
    path = m.export_report(kind, tmp_path / f'{kind}.csv')
    with path.open(newline='') as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == 1
    assert rows[0]['student_id'] == str(student.id)
    assert ('amount' in rows[0]) == (kind == 'finance')


def test_empty_export_and_invalid_kind(fresh_manager, tmp_path):
    """Empty reports retain headers; invalid kinds do not create a file."""
    path = fresh_manager.export_report('finance', tmp_path / 'empty.csv')
    assert path.read_text().startswith('student_id,amount,method,timestamp')
    with pytest.raises(ValueError):
        fresh_manager.export_report('unknown', tmp_path / 'bad.csv')
    assert not (tmp_path / 'bad.csv').exists()


def test_day_and_student_filters(school):
    """Only enrolled students and their courses on the selected day are offered."""
    m, alice, piano = school
    t = m.add_teacher('Fret', 'Guitar')
    guitar = m.add_course('Guitar', 'Guitar', t.id)
    m.add_lesson(guitar.id, 'Wednesday', '11:00', 'B')
    bob = m.add_student('Bob')
    m.enrol_student(bob.id, guitar.id)
    assert m.students_on_day('Monday') == [alice]
    assert m.students_on_day('Wednesday') == [bob]
    assert m.student_courses_on_day(alice.id, 'Monday') == [piano]
    assert m.student_courses_on_day(alice.id, 'Wednesday') == []
    assert m.students_on_day('Friday') == []


def test_check_in_rejects_invalid_choices(school):
    """Backend validation protects against bypassing the filtered GUI."""
    m, student, course = school
    outsider = m.add_student('Unenrolled')
    for args in [(999, course.id, 'Monday'), (outsider.id, course.id, 'Monday'), (student.id, course.id, 'Friday')]:
        with pytest.raises(ValueError):
            m.check_in(*args)
    assert not m.attendance_log


def test_ids_continue_after_delete_and_restart(school):
    """Persisted counters do not reuse the highest deleted student ID."""
    m, student, _ = school
    m.remove_student(student.id)
    loaded = ScheduleManager(m.data_path)
    assert loaded.add_student('Next').id == student.id + 1
    assert loaded.add_teacher('Next teacher', 'Flute').id == 2
    assert loaded.add_course('More Piano', 'Piano', 1).id == 2


def test_failed_save_rolls_back(school, monkeypatch):
    """A failed disk save must not leave an unsaved payment in memory."""
    m, student, _ = school
    before = m.data_path.read_bytes()
    def fail():
        raise OSError('disk unavailable')
    monkeypatch.setattr(m, '_save_data', fail)
    with pytest.raises(OSError):
        m.record_payment(student.id, 10, 'Cash')
    assert m.finance_log == []
    assert m.data_path.read_bytes() == before


def test_cancel_lesson_and_log(school, caplog):
    """Cancellation removes the lesson from rosters and records its reason."""
    m, _, course = school
    with caplog.at_level(logging.INFO):
        m.cancel_lesson(course.lessons[0]['lesson_id'], 'Teacher absent')
    assert m.daily_roster('Monday') == []
    assert 'Teacher absent' in caplog.text


def test_backup_preserves_bytes_and_unique_names(school, tmp_path):
    """Backups are distinct and byte-identical to the source."""
    m, _, _ = school
    folder = tmp_path / 'backups'
    assert backup_data(m.data_path, folder)
    assert backup_data(m.data_path, folder)
    files = list(folder.iterdir())
    assert len(files) == 2
    assert all(p.read_bytes() == m.data_path.read_bytes() for p in files)
    assert not backup_data(tmp_path / 'missing.json', folder)


def test_logger_is_repeat_safe(tmp_path):
    """Repeated initialisation does not append duplicate file handlers."""
    path = tmp_path / 'test.log'
    logger = init_logger(path)
    init_logger(path)
    handlers = [h for h in logger.handlers if isinstance(h, logging.FileHandler) and h.baseFilename == str(path)]
    assert len(handlers) == 1
    logging.info('test event')
    assert 'test event' in path.read_text()
    logger.removeHandler(handlers[0])
    handlers[0].close()


def test_corrupt_json_is_not_overwritten(tmp_path):
    """Loading invalid JSON fails clearly while preserving the original file."""
    path = tmp_path / 'broken.json'
    path.write_text('{invalid')
    with pytest.raises(ValueError):
        ScheduleManager(path)
    assert path.read_text() == '{invalid'
