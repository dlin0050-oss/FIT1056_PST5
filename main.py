"""PST5 entry point: initialise logging and session backup before launching the GUI."""
from pathlib import Path
import streamlit as st
from app.admin_utils import init_logger, backup_data
from gui.main_dashboard import launch


def main():
    """Initialise administration once per browser session, then render the dashboard."""
    root = Path(__file__).resolve().parent
    init_logger(root / 'logs/msms.log')
    # Streamlit executes this file repeatedly. Back up once per session, not per click.
    if not st.session_state.get('startup_backup_done', False):
        st.session_state['startup_backup_ok'] = backup_data(root / 'data/msms.json', root / 'data/backups')
        st.session_state['startup_backup_done'] = True
    launch()
    if not st.session_state.get('startup_backup_ok', False):
        st.warning('Startup backup could not be created. Check the data file and folder permissions.')


if __name__ == '__main__':
    main()
