"""gui/course_pages.py: Music School Management System module."""
import streamlit as st
from gui.common import choose, action

DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']


def show_course_management_page(manager):
    """Render courses and forms for course creation and lesson scheduling."""
    st.header('Course Management')
    rows = [{'ID': c.id, 'Name': c.name, 'Instrument': c.instrument, 'Teacher ID': c.teacher_id, 'Student IDs': ', '.join(map(str, c.enrolled_student_ids))} for c in manager.courses]
    if rows:
        st.dataframe(rows, hide_index=True, width='stretch')
    else:
        st.info('No courses yet.')
    if manager.teachers:
        with st.form('add_course'):
            name = st.text_input('Course name')
            instrument = st.text_input('Instrument')
            tid = choose('Teacher', manager.teachers, 'course_teacher')
            if st.form_submit_button('Add Course'):
                action(manager.add_course, name, instrument, tid)
    else:
        st.info('Add a teacher before creating a course.')
    if manager.courses:
        st.subheader('Schedule a lesson')
        with st.form('add_lesson'):
            cid = choose('Course', manager.courses, 'lesson_course')
            day = st.selectbox('Day', DAYS)
            time = st.time_input('Start time')
            room = st.text_input('Room')
            if st.form_submit_button('Add Lesson'):
                action(manager.add_lesson, cid, day, time.strftime('%H:%M'), room)
        st.caption('Conflict checking covers the same teacher or room at an identical start time. Lesson durations are not modelled.')

    lessons = [(c, lesson) for c in manager.courses for lesson in c.lessons]
    if lessons:
        st.subheader('Cancel a lesson')
        lesson_id = st.selectbox('Lesson', [l['lesson_id'] for c, l in lessons],
            format_func=lambda lid: next(f"{c.name}: {l['day']} {l['start_time']} (ID {lid})" for c, l in lessons if l['lesson_id'] == lid))
        with st.form('cancel_lesson'):
            reason = st.text_input('Cancellation reason')
            if st.form_submit_button('Cancel Lesson'):
                action(manager.cancel_lesson, lesson_id, reason)
