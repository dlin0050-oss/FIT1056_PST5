"""gui/common.py: Music School Management System module."""
import streamlit as st


def choose(label, records, key):
    """Display ID-backed record choices and discard invalid previous selections."""
    ids = [r.id for r in records]
    if key in st.session_state and st.session_state[key] not in ids:
        del st.session_state[key]
    return st.selectbox(label, [r.id for r in records], format_func=lambda i: next(f'{r.name} (ID {r.id})' for r in records if r.id == i), key=key)


def action(function, *args, success_flag=None):
    """Execute a manager operation, preserve success feedback and handle errors."""
    try:
        function(*args)
        if success_flag:
            st.session_state[success_flag] = True
        st.session_state['notice'] = 'Saved successfully.'
        st.rerun()
    except (ValueError, OSError) as error:
        st.error(str(error))
