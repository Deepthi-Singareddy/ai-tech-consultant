@echo off
echo ======================================================================
echo  PUSHING AI TECH CONSULTANT TO GITHUB
echo  Target: https://github.com/Deepthi-Singareddy/ai-tech-consultant.git
echo ======================================================================

git push -u origin main

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ======================================================================
    echo  SUCCESSFULLY PUSHED TO GITHUB!
    echo  View at: https://github.com/Deepthi-Singareddy/ai-tech-consultant
    echo ======================================================================
) else (
    echo.
    echo ======================================================================
    echo  Push failed. Make sure you have created the empty repository:
    echo  https://github.com/new?name=ai-tech-consultant
    echo ======================================================================
)
pause
