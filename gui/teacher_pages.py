"""gui/teacher_pages.py: Music School Management System module."""
import streamlit as st
from gui.common import choose, action


def show_teacher_management_page(manager):
    """Render teacher search, creation, updates and safe removal."""
    st.header('Teacher Management')
    term = st.text_input('Find teachers by name or speciality')
    rows = [t.__dict__ for t in manager.find_teachers(term)]
    if rows:
        st.dataframe(rows, hide_index=True, width='stretch')
    else:
        st.info('No matching teachers.')
    with st.form('add_teacher'):
        name = st.text_input('Teacher name')
        speciality = st.text_input('Speciality')
        if st.form_submit_button('Add Teacher'):
            action(manager.add_teacher, name, speciality)
    if manager.teachers:
        tid = choose('Teacher to manage', manager.teachers, 'edit_teacher')
        teacher = next(t for t in manager.teachers if t.id == tid)
        with st.form(f'update_teacher_{tid}'):
            name = st.text_input('New name', value=teacher.name)
            speciality = st.text_input('New speciality', value=teacher.speciality)
            if st.form_submit_button('Update Teacher'):
                action(manager.update_teacher, tid, name, speciality)
        confirm = st.checkbox('Remove this teacher', key=f'remove_teacher_{tid}')
        if st.button('Remove Teacher', disabled=not confirm):
            action(manager.remove_teacher, tid)
        st.caption('Teachers assigned to courses cannot be removed.')
