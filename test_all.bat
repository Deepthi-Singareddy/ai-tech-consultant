@echo off
echo ======================================================================
echo  RUNNING COMPLETE UNIT TEST SUITE ACROSS ALL 3 TASKS
echo ======================================================================

echo [1/3] Testing Task 1: Knowledge Brain (pytest)...
python -m pytest task1-knowledge-brain/tests/test_knowledge_brain.py -v
if %ERRORLEVEL% NEQ 0 (
    echo Task 1 tests failed!
    exit /b %ERRORLEVEL%
)

echo.
echo [2/3] Testing Task 2: Inbox Agent (TypeScript node runner)...
cd task2-inbox-agent && call npx tsx tests/inbox.test.ts && cd ..
if %ERRORLEVEL% NEQ 0 (
    echo Task 2 tests failed!
    exit /b %ERRORLEVEL%
)

echo.
echo [3/3] Testing Task 3: Meeting to Scope (pytest)...
python -m pytest task3-meeting-to-scope/tests/test_meeting_to_scope.py -v
if %ERRORLEVEL% NEQ 0 (
    echo Task 3 tests failed!
    exit /b %ERRORLEVEL%
)

echo.
echo ======================================================================
echo  ALL TESTS PASSED ACROSS TASKS 1, 2, AND 3! (16/16 TESTS)
echo ======================================================================
pause
