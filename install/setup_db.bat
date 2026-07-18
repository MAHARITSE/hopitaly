@echo off
REM Configurer la base de données HealthNet
cd /d "%~dp0.."
echo Migration de la base...
python manage.py migrate
if not errorlevel 1 (
    echo Base configurée avec succès.
) else (
    echo Erreur lors de la migration.
)
pause
