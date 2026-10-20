"""gui/main_dashboard.py: Music School Management System module."""
import streamlit as st
from app.schedule import ScheduleManager
from gui.student_pages import show_student_management_page
from gui.teacher_pages import show_teacher_management_page
from gui.course_pages import show_course_management_page
from gui.roster_pages import show_roster_page
from gui.finance_pages import show_finance_page


def launch():
    """Configure the dashboard, preserve the manager and route navigation."""
    st.set_page_config(page_title='Music School Management System', layout='wide')
    st.title('Music School Management System')
    if 'manager' not in st.session_state:
        try:
            st.session_state.manager = ScheduleManager()
        except (ValueError, OSError, TypeError) as error:
            st.error(f'Cannot load data: {error}')
            st.stop()
    manager = st.session_state.manager
    if 'notice' in st.session_state:
        st.success(st.session_state.pop('notice'))
    st.sidebar.title('MSMS Navigation')
    page = st.sidebar.radio('Go to', ['Student Management', 'Teacher Management', 'Course Management', 'Daily Roster', 'Payments'])
    pages = {'Student Management': show_student_management_page, 'Teacher Management': show_teacher_management_page, 'Course Management': show_course_management_page, 'Daily Roster': show_roster_page, 'Payments': show_finance_page}
    if page in pages:
        pages[page](manager)
    else:
        st.header('Payments')
        show_finance_page(manager)
