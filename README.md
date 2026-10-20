# Music School Management System — PST5

This cumulative FIT1056 project upgrades the submitted PST4 application with finance, administration and automated quality checks. Earlier student, teacher, course, enrolment, search, student card and attendance features remain available.

## Run on Windows

Open the project folder in VS Code and run these commands in its terminal:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run main.py
```

Open the Local URL printed by Streamlit. Stop with Ctrl+C. On macOS/Linux, create the environment with `python3 -m venv .venv` and substitute `.venv/bin/python` for the Windows Python path.

## Automated tests

Run from the project root:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

`pytest.ini` configures discovery and the import path. Tests use pytest's `tmp_path`, so they never change `data/msms.json`. Backend tests cover course creation, payments, histories, CSV headers/content, invalid input, enrolment/day filters, persistent IDs, failed-save rollback, cancellation logging, backups and corrupt JSON. Streamlit AppTest checks form reset, dependent selectors, payment/history interaction and empty pages. These tests follow Arrange, Act, Assert; fixtures arrange reusable school records.

## Changes requested in PST4 feedback

- Registration fields clear only after a successful save. Failed registration preserves input for correction.
- Selecting a weekday shows only lessons scheduled for that day.
- Check-in students are restricted to those enrolled in a course running that day.
- After selecting a student, only that student's enrolled courses running that day are offered.
- Dependent dropdowns sit outside forms so they update immediately when their parent choice changes. IDs distinguish people with identical names.
- Source modules and functions have documentation; comments explain state resets, validation, persistence and backup timing.

## PST5 requirements and implementation

| Part | Implementation |
| --- | --- |
| 5.1 Finance and reporting | `finance_log` is loaded/saved; `record_payment`, `get_payment_history`, `export_report` are methods of ScheduleManager |
| 5.2 Finance GUI | `show_finance_page` replaces Payments (stub); payment form, student history, CSV downloads |
| 5.3 Admin utilities | `init_logger(log_file)` and `backup_data(data_path, backup_dir)` in `app/admin_utils.py` |
| Lifecycle integration (labelled 5.4 in the PDF) | `main.py` sets logging and attempts one startup backup per browser session before launching the dashboard; registration, payment and cancellation events are logged |
| Automated tests (also labelled 5.4 in the PDF) | Backend pytest tests and Streamlit interaction tests in `tests/` |

The original template's `create_course` name is provided as an alias for the existing `add_course` method. Tests create a teacher first; courses cannot refer to nonexistent teachers. Lesson cancellation is accessible through Course Management and logged with a reason.

## Files

- `main.py`: logging, startup backup and GUI entry point.
- `app/user.py`, `app/student.py`, `app/teacher.py`: retained OOP models.
- `app/schedule.py`: validation, school operations, JSON persistence, finance, reports and cancellation.
- `app/admin_utils.py`: idempotent file logging and timestamped backups.
- `gui/main_dashboard.py`: navigation and session-state manager.
- `gui/student_pages.py`: student search, registration, updates, removal, enrolment, transfer and cards.
- `gui/teacher_pages.py`: teacher search and management.
- `gui/course_pages.py`: courses, scheduling and cancellation.
- `gui/roster_pages.py`: weekday roster and filtered check-in.
- `gui/finance_pages.py`: payments, history, report downloads and Backup Now.
- `gui/common.py`: ID-backed selectors and shared operation feedback.
- `data/msms.json`: submitted PST4 data; existing attendance is retained.
- `tests/`: isolated backend and GUI tests.

## Data, validation and limitations

The manager lives in Streamlit session state across interactions. JSON persists between restarts. Automatic student, teacher, course and lesson counters are restored and saved; deleted IDs are not reused. Older PST4 data without finance/counter fields loads with safe defaults. New finance/counter fields are written on the next successful mutation.

Student enrolments are authoritative when legacy course lists disagree; course membership lists are rebuilt on loading. Historical attendance is preserved. Registration uses the first course matching the instrument; alternatively add an unenrolled student and enrol them in an explicitly selected course. Search is case-insensitive and supports partial names; an empty search lists all records.

Payments are local records only, not real card processing. Amounts must be numeric, finite and positive; values round to two decimal places. Payment method is required. Deleted students' payment and attendance records are retained for reports. The history GUI selects current students; retained historical IDs remain available through the manager API and CSV exports.

Invalid operations raise readable errors. JSON writes use a temporary file and atomic replacement. A decorator snapshots manager state and restores it when a mutation fails, including a disk save failure. Malformed JSON is not silently replaced; correct or restore the file before restarting. Validation covers expected record structure but does not guarantee recovery from every conceivable manually corrupted value.

Attendance uses the current timestamp and validates the selected weekday's schedule, not the actual calendar date. Selecting Monday means the recurring Monday timetable. The optional `day` argument preserves older callers; the GUI always supplies it. Duplicate check-ins remain allowed. Lesson cancellation removes the scheduled lesson; logs retain its reason. Room/teacher conflict checks compare identical start times only because lesson durations are not modelled.

Logs are generated at `logs/msms.log`. Backups are generated in `data/backups/` with microsecond timestamps. Backups occur once per browser session rather than on every Streamlit rerun; Backup Now provides an extra manual copy. If startup backup fails, a warning appears and the app remains usable. Logging handlers are not duplicated on reruns. Backups and logs are excluded from Git and the deliverable ZIP. To restore, stop the app, keep a copy of the current data, copy the chosen backup over `data/msms.json`, then restart.

This local JSON prototype is for one receptionist. Concurrent sessions do not coordinate edits. Logging/backup and automated tests improve reliability; they do not make arbitrary OS or hardware failures impossible.

## Manual verification

1. Register a Piano student. Confirm the record appears and the two registration fields clear. Try an unavailable instrument and confirm the input remains with an error.
2. In Daily Roster select Tuesday. Only Tuesday lessons should appear; only students enrolled in those courses should be offered. Select another student or weekday and check the course list updates. An empty day should show a message instead of a check-in button.
3. Record a payment under Payments. Select the student and click View History. Download finance and attendance CSVs and open them.
4. Use Backup Now and verify a new backup exists. Check `logs/msms.log` for registration/payment/backup entries.
5. Add and cancel a lesson with a reason. Confirm it disappears from that day's roster and a cancellation event appears in the log.
6. Restart and confirm records persist. Run the automated test command.

## Git and submission

Use branch `individual` and preserve previous commits. For a separate PST5 folder, copy the existing working repository including its `.git`, then copy the upgraded source files into it. Do not copy an old virtual environment to a renamed folder; create a new `.venv` using the commands above.

The delivered code is already complete. Commit current changes honestly in coherent groups; do not backdate commits. For future work, complete and test each fragment before committing. The ZIP includes `GIT_STEPS.md` with the checkpoint command messages read from the supplied PDF, plus commands for the feedback fixes and extra files. Review `git status` and existing commits before using them, especially if you have already committed anything.

Set the remote to the intended PST5 repository before pushing; copying PST4's repository preserves its old remote until you change it. Check `git remote -v`, then `git push -u origin individual` once the destination is correct. Do not force-push to work around a rejection.

Package source, `data`, tests, requirements, configuration and documentation. Exclude `.git`, `.venv`, `__pycache__`, `.pytest_cache`, logs and backups. A ZIP can be generated from committed tracked files with `git archive --format=zip --output=../PST5_Submission.zip HEAD` after reviewing tracked files and committing the intended data. Upload the final ZIP to Moodle and complete its submit step separately from Git push.
