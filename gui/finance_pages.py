"""PST5 payment entry, per-student history, CSV downloads and manual backup."""
from pathlib import Path
from tempfile import TemporaryDirectory
import streamlit as st
from app.admin_utils import backup_data
from gui.common import choose, action


def show_finance_page(manager):
    """Expose finance and administrative tools without executing real transactions."""
    st.header('Finance & Payments')
    if manager.students:
        st.subheader('Record New Payment')
        with st.form('payment_form', clear_on_submit=True):
            sid = choose('Student', manager.students, 'payment_student')
            amount = st.number_input('Payment Amount', min_value=0.01, value=100.0, step=0.01)
            method = st.text_input('Payment Method (e.g., Credit Card, Cash)')
            if st.form_submit_button('Record Payment'):
                action(manager.record_payment, sid, amount, method)
        st.subheader('View Student Payment History')
        sid = choose('Student to View History', manager.students, 'history_student')
        with st.form('payment_history'):
            if st.form_submit_button('View History'):
                st.session_state['history_for'] = sid
        if st.session_state.get('history_for') == sid:
            history = manager.get_payment_history(sid)
            if history:
                st.dataframe(history, hide_index=True, width='stretch')
            else:
                st.info('This student has no payment history.')
    else:
        st.info('Add a student before recording a payment.')
    st.subheader('Export Reports')
    kind = st.selectbox('Report type', ['finance', 'attendance'])
    # Generate a short-lived local file; the user chooses where to save the download.
    try:
        with TemporaryDirectory() as folder:
            path = manager.export_report(kind, Path(folder) / f'{kind}.csv')
            st.download_button('Download CSV', path.read_bytes(), file_name=f'{kind}.csv', mime='text/csv')
    except (OSError, ValueError) as error:
        st.error(f'Could not export report: {error}')
    if st.button('Backup Now'):
        if backup_data(manager.data_path, manager.data_path.parent / 'backups'):
            st.success('Backup created.')
        else:
            st.error('Backup failed. Check the data file and folder permissions.')
