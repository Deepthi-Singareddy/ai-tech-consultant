@echo off
echo ======================================================================
echo  RUNNING COMPLETE EVALUATION HARNESS ACROSS ALL 3 TASKS (70 CASES)
echo ======================================================================

echo [1/3] Running Task 1 Evaluations (25 test cases)...
python task1-knowledge-brain/evals/run_evals.py

echo.
echo [2/3] Running Task 2 Evaluations (25 test cases)...
cd task2-inbox-agent && call npx tsx evals/run_evals.ts && cd ..

echo.
echo [3/3] Running Task 3 Evaluations (20 test cases)...
python task3-meeting-to-scope/evals/run_evals.py

echo.
echo ======================================================================
echo  ALL 70 EVALUATION CASES EXECUTED! METRICS SAVED TO EVAL RESULTS JSON.
echo ======================================================================
pause
