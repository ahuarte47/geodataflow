
SET APP_SCRIPT_PATH=%~dp0
IF %APP_SCRIPT_PATH:~-1%==\ SET APP_SCRIPT_PATH=%APP_SCRIPT_PATH:~0,-1%
SET PACKAGE_FOLDER=%APP_SCRIPT_PATH%/../geodataflow

REM ===========================================================================
REM Cleaning everything

@echo OFF
FOR /d /r "%PACKAGE_FOLDER%" %%d IN (__pycache__) DO @IF EXIST "%%d" rmdir /s /q "%%d"
@echo OFF

@echo INFO: Cleaning everything

rmdir /s /q "%PACKAGE_FOLDER%/core/dist"
rmdir /s /q "%PACKAGE_FOLDER%/core/geodataflow.core.egg-info"

rmdir /s /q "%PACKAGE_FOLDER%/spatial/dist"
rmdir /s /q "%PACKAGE_FOLDER%/spatial/geodataflow.spatial.egg-info"

rmdir /s /q "%PACKAGE_FOLDER%/dataframes/dist"
rmdir /s /q "%PACKAGE_FOLDER%/dataframes/geodataflow.dataframes.egg-info"

rmdir /s /q "%PACKAGE_FOLDER%/api/dist"
rmdir /s /q "%PACKAGE_FOLDER%/api/geodataflow.api.egg-info"

rmdir /s /q "%PACKAGE_FOLDER%/all/dist"
rmdir /s /q "%PACKAGE_FOLDER%/all/geodataflow.egg-info"

REM ===========================================================================
