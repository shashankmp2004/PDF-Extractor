@echo off
REM Build and run script for PDF Outline Extractor (Windows)

echo 🐳 PDF Outline Extractor - Build ^& Run
echo ======================================

REM Check if Docker is running
docker info >nul 2>&1
if errorlevel 1 (
    echo ❌ Error: Docker is not running. Please start Docker first.
    exit /b 1
)

REM Build the Docker image
echo 🔨 Building Docker image...
docker build -t pdf-extractor .

if errorlevel 1 (
    echo ❌ Failed to build Docker image
    exit /b 1
)

echo ✅ Docker image built successfully!

REM Create input and output directories if they don't exist
if not exist "input" mkdir input
if not exist "output" mkdir output

REM Check if there are any PDF files in input directory
set pdf_count=0
for %%f in (input\*.pdf) do set /a pdf_count+=1

if %pdf_count%==0 (
    echo ⚠️  No PDF files found in .\input\ directory
    echo    Please add some PDF files to process
    echo.
    echo 📁 Current directory structure:
    dir /b
    echo.
    echo To run the extractor once you have PDFs:
    echo docker run -v %cd%/input:/app/input -v %cd%/output:/app/output pdf-extractor
) else (
    echo 📄 Found %pdf_count% PDF file(s) in .\input\
    echo 🚀 Running PDF extraction...
    
    REM Run the container
    docker run --rm -v "%cd%/input:/app/input" -v "%cd%/output:/app/output" pdf-extractor
    
    if errorlevel 1 (
        echo ❌ PDF extraction failed
        exit /b 1
    )
    
    echo.
    echo ✅ PDF extraction completed!
    echo 📁 Output files:
    dir /b output\
)

echo.
echo 🎉 Ready to process PDFs!
