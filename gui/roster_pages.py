"""Daily timetable and dependent student/course check-in selectors (PST4 feedback)."""
import streamlit as st
from gui.common import choose, action
from gui.course_pages import DAYS


def show_roster_page(manager):
    """Filter by weekday, then student, then their scheduled enrolled courses."""
    st.header('Daily Roster')
    day = st.selectbox('Select a day', DAYS, key='roster_day')
    rows = manager.daily_roster(day)
    if rows:
        st.dataframe(rows, hide_index=True, width='stretch')
    else:
        st.info('No lessons scheduled for this day.')
    st.subheader('Student Check-in')
    students = manager.students_on_day(day)
    if students:
        # Selectors stay outside a form: changing the student must immediately
        # rerun the page so that the course list is recalculated before check-in.
        sid = choose('Student with classes on this day', students, 'attendance_student')
        courses = manager.student_courses_on_day(sid, day)
        cid = choose('Enrolled course on this day', courses, 'attendance_course')
        if st.button('Check-in Student'):
            action(manager.check_in, sid, cid, day)
    else:
        st.info('No enrolled students have classes on this day.')
    with st.expander('Attendance history'):
        if manager.attendance_log:
            rows = [{**r, 'student_id': str(r['student_id']), 'course_id': str(r['course_id'])} for r in manager.attendance_log]
            st.dataframe(rows, hide_index=True, width='stretch')
        else:
            st.info('No attendance records.')
