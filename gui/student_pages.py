"""gui/student_pages.py: Music School Management System module."""
import streamlit as st
from gui.common import choose, action


def show_student_management_page(manager):
    # Reset widget values before recreating the form, only after a successful save.
    """Render student search, registration and cumulative management operations."""
    if st.session_state.pop('registration_saved', False):
        st.session_state['register_name'] = ''
        st.session_state['register_instrument'] = ''
    st.header('Student Management')
    term = st.text_input('Find students by name')
    students = manager.find_students(term)
    rows = [{'ID': s.id, 'Name': s.name, 'Courses': ', '.join(c.name for c in manager.courses if c.id in s.enrolled_course_ids)} for s in students]
    if rows:
        st.dataframe(rows, hide_index=True, width='stretch')
    else:
        st.info('No matching students.')
    with st.expander('Register student and first instrument', expanded=True):
        st.caption('Registration selects the first available course for the instrument. Use Enrol or Switch to choose another course.')
        with st.form('register'):
            name = st.text_input('Student name', key='register_name')
            instrument = st.text_input('First instrument', key='register_instrument')
            if st.form_submit_button('Register Student'):
                action(manager.register_new_student, name, instrument, success_flag='registration_saved')
    with st.expander('Add student without enrolment'):
        with st.form('add_student'):
            name = st.text_input('Name')
            if st.form_submit_button('Add Student'):
                action(manager.add_student, name)
    if not manager.students:
        return
    with st.expander('Update or remove student'):
        sid = choose('Student', manager.students, 'edit_student')
        student = manager.find_student_by_id(sid)
        with st.form(f'edit_student_{sid}'):
            name = st.text_input('New name', value=student.name)
            if st.form_submit_button('Update Student'):
                action(manager.update_student, sid, name)
        confirm = st.checkbox('Remove this student and their current enrolments', key=f'delete_{sid}')
        if st.button('Remove Student', disabled=not confirm):
            action(manager.remove_student, sid)
    with st.expander('Student ID card'):
        sid = choose('Student', manager.students, 'card_student')
        card = manager.student_card(sid)
        st.text(card)
        st.download_button('Download Student Card', card, file_name=f'{sid}_card.txt', mime='text/plain')
    if manager.courses:
        with st.expander('Enrol existing student'):
            with st.form('enrol'):
                sid = choose('Student', manager.students, 'enrol_student')
                cid = choose('Course', manager.courses, 'enrol_course')
                if st.form_submit_button('Enrol Student'):
                    action(manager.enrol_student, sid, cid)
        with st.expander('Switch student course'):
            with st.form('switch'):
                sid = choose('Student', manager.students, 'switch_student')
                old = choose('From course', manager.courses, 'switch_from')
                new = choose('To course', manager.courses, 'switch_to')
                if st.form_submit_button('Switch Course'):
                    action(manager.switch_course, sid, old, new)
