# Git checkpoints

Use your existing `individual` branch. Run `git status` first and review any changes already staged. Commands below group the completed working tree; they do not recreate past development. Test locally before committing. Do not run another `git init` in an existing repository.

## 1. Backend (PDF Fragment 5.1 message)

```powershell
git add app/schedule.py app/user.py app/student.py app/teacher.py app/__init__.py requirements.txt .gitignore
git commit -m "feat(finance): Implement core finance tracking and CSV reporting logic"
```

This backend also includes logging calls, validation and the roster filters requested in feedback.

## 2. Admin utilities (PDF Fragment 5.3 message)

Commit the utility before the GUI that imports it, so imports remain resolvable.

```powershell
git add app/admin_utils.py
git commit -m "feat(admin): Add logging and data backup utilities"
```

## 3. Feedback fixes and existing page documentation

```powershell
git add gui/common.py gui/student_pages.py gui/roster_pages.py gui/course_pages.py gui/teacher_pages.py gui/__init__.py
git commit -m "fix(gui): clear registration and filter daily check-in choices"
```

## 4. Finance page (PDF Fragment 5.2 message)

```powershell
git add gui/finance_pages.py gui/main_dashboard.py
git commit -m "feat(gui): Build finance page for recording payments and viewing history"
```

## 5. Lifecycle integration

The PDF's lifecycle checkpoint message refers to attendance persistence; this message describes the actual startup change instead.

```powershell
git add main.py
git commit -m "feat(admin): integrate startup logging and session backups"
```

## 6. Automated tests (PDF test-suite message)

```powershell
.\.venv\Scripts\python.exe -m pytest -q
git add tests pytest.ini
git commit -m "test(qa): Implement unit tests for core logic, completing PST5"
```

## 7. Documentation and final data review

```powershell
git add README.md GIT_STEPS.md
git commit -m "docs: explain PST5 setup tests and feedback fixes"
git status
git remote -v
git log --oneline -7
```

If `data/msms.json` changed during manual tests, inspect it before deciding whether to commit the test records. Do not discard data blindly. Check the intended PST5 repository address before changing origin or pushing. Once correct:

```powershell
git push -u origin individual
```

Do not include virtual environments, logs, backups or caches in Git or submission ZIPs.
