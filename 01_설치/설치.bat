@echo off
chcp 65001 > nul
echo ============================================
echo  python-hwpx 오프라인 설치
echo ============================================
echo.
python -V
if errorlevel 1 (
  echo [X] 파이썬이 없습니다. 먼저 python.org 에서 3.10 이상을 설치하세요.
  pause & exit /b
)
echo.
echo 인터넷을 쓰지 않고 wheels 폴더에서만 설치합니다...
python -m pip install --no-index --find-links "%~dp0wheels" python-hwpx
echo.
python -c "import hwpx; print('[O] python-hwpx', hwpx.__version__ if hasattr(hwpx,'__version__') else 'OK'); import lxml.etree; print('[O] lxml', lxml.etree.__version__)"
if errorlevel 1 (
  echo.
  echo [X] 실패. 파이썬 버전에 맞는 lxml wheel 이 없을 수 있습니다.
  echo     wheels 폴더에 cp310~cp314 가 있습니다. python -V 로 확인하세요.
  echo     그 버전이 없으면: python -m pip install lxml   ^(인터넷 필요^)
)
echo.
pause
