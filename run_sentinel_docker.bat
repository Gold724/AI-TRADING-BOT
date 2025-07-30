@echo off
setlocal enabledelayedexpansion

:: Default values
set DOCKER_IMAGE=sentinel-bot
set CONTAINER_NAME=sentinel-runner
set DOCKERFILE=Dockerfile.sentinel
set PORT=5000
set COMMAND=

:: Parse command line arguments
:parse_args
if "%~1"=="" goto check_command

if /i "%~1"=="-h" (
    goto show_help
) else if /i "%~1"=="--help" (
    goto show_help
) else if /i "%~1"=="-i" (
    set DOCKER_IMAGE=%~2
    shift
    shift
    goto parse_args
) else if /i "%~1"=="--image" (
    set DOCKER_IMAGE=%~2
    shift
    shift
    goto parse_args
) else if /i "%~1"=="-c" (
    set CONTAINER_NAME=%~2
    shift
    shift
    goto parse_args
) else if /i "%~1"=="--container" (
    set CONTAINER_NAME=%~2
    shift
    shift
    goto parse_args
) else if /i "%~1"=="-f" (
    set DOCKERFILE=%~2
    shift
    shift
    goto parse_args
) else if /i "%~1"=="--dockerfile" (
    set DOCKERFILE=%~2
    shift
    shift
    goto parse_args
) else if /i "%~1"=="-p" (
    set PORT=%~2
    shift
    shift
    goto parse_args
) else if /i "%~1"=="--port" (
    set PORT=%~2
    shift
    shift
    goto parse_args
) else if /i "%~1"=="build" (
    set COMMAND=build
    shift
    goto parse_args
) else if /i "%~1"=="run" (
    set COMMAND=run
    shift
    goto parse_args
) else if /i "%~1"=="stop" (
    set COMMAND=stop
    shift
    goto parse_args
) else if /i "%~1"=="logs" (
    set COMMAND=logs
    shift
    goto parse_args
) else if /i "%~1"=="status" (
    set COMMAND=status
    shift
    goto parse_args
) else if /i "%~1"=="restart" (
    set COMMAND=restart
    shift
    goto parse_args
) else if /i "%~1"=="clean" (
    set COMMAND=clean
    shift
    goto parse_args
) else if /i "%~1"=="all" (
    set COMMAND=all
    shift
    goto parse_args
) else (
    echo Unknown option: %~1
    goto show_help
)

:check_command
if "%COMMAND%"=="" (
    echo Error: No command specified
    goto show_help
)

:: Execute command
if /i "%COMMAND%"=="build" (
    call :build_image
) else if /i "%COMMAND%"=="run" (
    call :run_container
) else if /i "%COMMAND%"=="stop" (
    call :stop_container
) else if /i "%COMMAND%"=="logs" (
    call :show_logs
) else if /i "%COMMAND%"=="status" (
    call :check_status
) else if /i "%COMMAND%"=="restart" (
    call :restart_container
) else if /i "%COMMAND%"=="clean" (
    call :clean_up
) else if /i "%COMMAND%"=="all" (
    call :build_image
    call :run_container
) else (
    echo Unknown command: %COMMAND%
    goto show_help
)

goto :eof

:: Function to show help
:show_help
echo AI Trading Sentinel Docker Helper Script
echo.
echo Usage: %0 [options] [command]
echo.
echo Commands:
echo   build       Build the Docker image
echo   run         Run the Docker container
echo   stop        Stop the running container
echo   logs        Show container logs
echo   status      Check container status
echo   restart     Restart the container
echo   clean       Remove container and image
echo   all         Build and run in one command
echo.
echo Options:
echo   -h, --help                Show this help message
echo   -i, --image NAME          Set Docker image name (default: %DOCKER_IMAGE%)
echo   -c, --container NAME      Set container name (default: %CONTAINER_NAME%)
echo   -f, --dockerfile FILE     Set Dockerfile to use (default: %DOCKERFILE%)
echo   -p, --port PORT           Set host port to map (default: %PORT%)
echo.
echo Example:
echo   %0 --port 8080 all        Build and run with port 8080
goto :eof

:: Function to build Docker image
:build_image
echo Building Docker image: %DOCKER_IMAGE% from %DOCKERFILE%
docker build -t %DOCKER_IMAGE% -f %DOCKERFILE% .
echo Build completed successfully
goto :eof

:: Function to run Docker container
:run_container
echo Running container: %CONTAINER_NAME% from image: %DOCKER_IMAGE% on port: %PORT%

:: Check if container already exists
docker ps -a --format "{{.Names}}" | findstr /b /c:"%CONTAINER_NAME%" >nul
if not errorlevel 1 (
    echo Container %CONTAINER_NAME% already exists. Stopping and removing...
    docker stop %CONTAINER_NAME% 2>nul || echo Container not running
    docker rm %CONTAINER_NAME% 2>nul || echo Failed to remove container
)

:: Create necessary directories
if not exist logs mkdir logs
if not exist temp_chrome_profile mkdir temp_chrome_profile

:: Run the container
docker run -d ^
    --name %CONTAINER_NAME% ^
    -p %PORT%:5000 ^
    -v "%cd%\logs:/app/logs" ^
    -v "%cd%\.env:/app/.env" ^
    -v "%cd%\temp_chrome_profile:/app/temp_chrome_profile" ^
    --restart unless-stopped ^
    %DOCKER_IMAGE%

echo Container started. Access the API at http://localhost:%PORT%
echo View logs with: %0 logs
goto :eof

:: Function to stop container
:stop_container
echo Stopping container: %CONTAINER_NAME%
docker stop %CONTAINER_NAME%
echo Container stopped
goto :eof

:: Function to show container logs
:show_logs
echo Showing logs for container: %CONTAINER_NAME%
docker logs -f %CONTAINER_NAME%
goto :eof

:: Function to check container status
:check_status
echo Checking status of container: %CONTAINER_NAME%

docker ps --format "{{.Names}}" | findstr /b /c:"%CONTAINER_NAME%" >nul
if not errorlevel 1 (
    echo Container is running
    docker ps --filter "name=%CONTAINER_NAME%" --format "table {{.ID}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}"
    
    :: Check health status if available
    for /f "tokens=*" %%i in ('docker inspect --format="{{if .State.Health}}{{.State.Health.Status}}{{else}}N/A{{end}}" %CONTAINER_NAME%') do set HEALTH=%%i
    echo Health status: !HEALTH!
) else (
    echo Container is not running
    
    :: Check if container exists but is stopped
    docker ps -a --format "{{.Names}}" | findstr /b /c:"%CONTAINER_NAME%" >nul
    if not errorlevel 1 (
        echo Container exists but is stopped
        docker ps -a --filter "name=%CONTAINER_NAME%" --format "table {{.ID}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}"
    ) else (
        echo Container does not exist
    )
)
goto :eof

:: Function to restart container
:restart_container
echo Restarting container: %CONTAINER_NAME%
docker restart %CONTAINER_NAME%
echo Container restarted
goto :eof

:: Function to clean up container and image
:clean_up
echo Cleaning up container and image

:: Stop and remove container if it exists
docker ps -a --format "{{.Names}}" | findstr /b /c:"%CONTAINER_NAME%" >nul
if not errorlevel 1 (
    echo Removing container: %CONTAINER_NAME%
    docker stop %CONTAINER_NAME% 2>nul || echo Container not running
    docker rm %CONTAINER_NAME%
)

:: Remove image if it exists
docker images --format "{{.Repository}}" | findstr /b /c:"%DOCKER_IMAGE%" >nul
if not errorlevel 1 (
    echo Removing image: %DOCKER_IMAGE%
    docker rmi %DOCKER_IMAGE%
)

echo Clean up completed
goto :eof