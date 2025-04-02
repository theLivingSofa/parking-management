@echo off
        echo Starting Parking Management System...
        REM Activate virtual environment (adjust '.venv' if needed)
        IF EXIST .venv\Scripts\activate (
            call .venv\Scripts\activate
        ) ELSE (
            echo Virtual environment '.venv' not found. Using system Python.
        )
        REM Run the Uvicorn server
        echo Launching server on [http://127.0.0.1:8000](http://127.0.0.1:8000)
        uvicorn app.main:app --host 127.0.0.1 --port 8000
        pause