"""Streamlit interaction checks for registration, roster filters and payments."""
from streamlit.testing.v1 import AppTest
from app.schedule import ScheduleManager


def make_app(tmp_path):
    """Arrange a small school with two independent student/course paths."""
    m = ScheduleManager(tmp_path / 'gui.json')
    t = m.add_teacher('Keys', 'Piano')
    piano = m.add_course('Piano', 'Piano', t.id)
    m.add_lesson(piano.id, 'Monday', '10:00', 'A')
    alice = m.register_new_student('Alice', 'Piano')
    t = m.add_teacher('Fret', 'Guitar')
    guitar = m.add_course('Guitar', 'Guitar', t.id)
    m.add_lesson(guitar.id, 'Monday', '11:00', 'B')
    m.add_lesson(guitar.id, 'Tuesday', '11:00', 'B')
    bob = m.register_new_student('Bob', 'Guitar')
    at = AppTest.from_string(
        'from gui.main_dashboard import launch\nlaunch()',
        default_timeout=15
    )
    at.session_state['manager'] = m
    at.run()
    assert not at.exception
    return at, m, alice, bob, piano, guitar


def test_registration_clears_only_after_success(tmp_path):
    """Successful registration clears fields; rejected registration preserves them."""
    at, m, *_ = make_app(tmp_path)
    at.text_input(key='register_name').set_value('New Student')
    at.text_input(key='register_instrument').set_value('Piano')
    next(b for b in at.button if b.label == 'Register Student').click().run()
    assert not at.exception
    assert len(m.students) == 3
    assert at.text_input(key='register_name').value == ''
    assert at.text_input(key='register_instrument').value == ''
    at.text_input(key='register_name').set_value('Keep My Name')
    at.text_input(key='register_instrument').set_value('Missing Instrument')
    next(b for b in at.button if b.label == 'Register Student').click().run()
    assert not at.exception
    assert at.error
    assert at.text_input(key='register_name').value == 'Keep My Name'
    assert len(m.students) == 3


def test_roster_recalculates_dependent_options(tmp_path):
    """Changing student/day restricts choices and removes invalid old selections."""
    at, m, alice, bob, piano, guitar = make_app(tmp_path)
    at.sidebar.radio[0].set_value('Daily Roster').run()
    assert at.selectbox(key='attendance_course').options == [f'Piano (ID {piano.id})']
    at.selectbox(key='attendance_student').set_value(bob.id).run()
    assert at.selectbox(key='attendance_course').options == [f'Guitar (ID {guitar.id})']
    at.selectbox(key='roster_day').set_value('Tuesday').run()
    assert at.selectbox(key='attendance_student').options == [f'Bob (ID {bob.id})']
    next(b for b in at.button if b.label == 'Check-in Student').click().run()
    assert m.attendance_log[-1]['student_id'] == bob.id
    assert m.attendance_log[-1]['course_id'] == guitar.id
    at.selectbox(key='roster_day').set_value('Friday').run()
    assert not at.exception
    assert not [s for s in at.selectbox if s.key == 'attendance_student']


def test_payments_and_history(tmp_path):
    """The payment form records data and the history section displays it."""
    at, m, *_ = make_app(tmp_path)
    at.sidebar.radio[0].set_value('Payments').run()
    next(t for t in at.text_input if 'Payment Method' in t.label).set_value('Cash')
    next(b for b in at.button if b.label == 'Record Payment').click().run()
    assert not at.exception
    assert len(m.finance_log) == 1
    next(b for b in at.button if b.label == 'View History').click().run()
    assert not at.exception
    assert at.dataframe


def test_all_pages_with_empty_data(tmp_path):
    """All six pages handle an empty school without invalid dropdown errors."""
    at = AppTest.from_string('from gui.main_dashboard import launch\nlaunch()')
    at.session_state['manager'] = ScheduleManager(tmp_path / 'empty.json')
    at.run()
    for page in at.sidebar.radio[0].options:
        at.sidebar.radio[0].set_value(page).run()
        assert not at.exception
