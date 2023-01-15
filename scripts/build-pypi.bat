
SET APP_SCRIPT_PATH=%~dp0
IF %APP_SCRIPT_PATH:~-1%==\ SET APP_SCRIPT_PATH=%APP_SCRIPT_PATH:~0,-1%
SET PACKAGE_FOLDER=%APP_SCRIPT_PATH%\..\geodataflow

REM ===========================================================================
REM Build installers

@echo OFF
FOR /d /r "%PACKAGE_FOLDER%" %%d IN (__pycache__) DO @IF EXIST "%%d" rmdir /s /q "%%d"
@echo OFF

@echo INFO: Building installers

REM geodataflow.core
rmdir /s /q "%PACKAGE_FOLDER%\core\dist"
rmdir /s /q "%PACKAGE_FOLDER%\core\geodataflow.core.egg-info"
python -m build "%PACKAGE_FOLDER%\core"

REM geodataflow.spatial
rmdir /s /q "%PACKAGE_FOLDER%\spatial\dist"
rmdir /s /q "%PACKAGE_FOLDER%\spatial\geodataflow.spatial.egg-info"
python -m build "%PACKAGE_FOLDER%\spatial"

REM geodataflow.dataframes
rmdir /s /q "%PACKAGE_FOLDER%\dataframes\dist"
rmdir /s /q "%PACKAGE_FOLDER%\dataframes\geodataflow.dataframes.egg-info"
python -m build "%PACKAGE_FOLDER%\dataframes"

REM geodataflow.api
rmdir /s /q "%PACKAGE_FOLDER%\api\dist"
rmdir /s /q "%PACKAGE_FOLDER%\api\geodataflow.api.egg-info"
python -m build "%PACKAGE_FOLDER%\api"

REM geodataflow.*
copy "%PACKAGE_FOLDER%\all\..\..\README.md" "%PACKAGE_FOLDER%\all\README.md"
copy "%PACKAGE_FOLDER%\all\..\..\LICENSE" "%PACKAGE_FOLDER%\all\LICENSE"
rmdir /s /q "%PACKAGE_FOLDER%\all\dist"
rmdir /s /q "%PACKAGE_FOLDER%\all\geodataflow.egg-info"
python -m build "%PACKAGE_FOLDER%\all"
del "%PACKAGE_FOLDER%\all\README.md"
del "%PACKAGE_FOLDER%\all\LICENSE"

REM ===========================================================================
REM Checking installlers

@echo OFF
FOR /d /r "%PACKAGE_FOLDER%" %%d IN (__pycache__) DO @IF EXIST "%%d" rmdir /s /q "%%d"
@echo ON

@echo INFO: Checking installers

twine check "%PACKAGE_FOLDER%\core\dist\*"
twine check "%PACKAGE_FOLDER%\spatial\dist\*"
twine check "%PACKAGE_FOLDER%\dataframes\dist\*"
twine check "%PACKAGE_FOLDER%\api\dist\*"
twine check "%PACKAGE_FOLDER%\all\dist\*"

REM ===========================================================================
