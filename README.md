# Cricsheet CSV-ZIP File Processor

A Flask web application designed to process and transform large ZIP files containing cricket match data from Cricsheet's experimental section.

![Flask](https://img.shields.io/badge/Flask-000000?style=for-the-badge&logo=flask&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black)

## Overview

This application provides a user-friendly interface for processing large ZIP files containing cricket match data from [Cricsheet's experimental section](https://cricsheet.org/downloads/#experimental). It handles the extraction, transformation, and combination of multiple CSV files into a single, properly formatted output file.

### Key Features

- 📤 Drag-and-drop or click-to-upload interface
- ⚡ Batch processing for efficient handling of large ZIP files
- 📊 Real-time progress tracking with detailed logs
- 🔄 Automatic data type conversion and normalization
- 💾 Downloads processed data in a pipe-separated format

## How It Works

1. **File Upload**: Users upload a ZIP file containing cricket match CSV data
2. **Processing Pipeline**:
   - Extracts files from ZIP archive
   - Processes files in batches of 500 for memory efficiency
   - Normalizes data types (converts numeric fields, handles missing values)
   - Combines processed data into a single output file
3. **Progress Tracking**: Real-time updates show:
   - Current processing status
   - Number of files processed
   - Detailed logs of operations
4. **Download**: Processed file available for download upon completion

## Technical Architecture

### Frontend
- HTML5 + CSS3 for the user interface
- JavaScript for handling file uploads and progress tracking
- Server-sent events for real-time progress updates

### Backend
- Flask web framework
- Pandas for data processing
- Python's built-in zipfile module for archive handling
- Threading for non-blocking file processing

## Installation & Deployment

### Local Development

1. Clone the repository
2. Install dependencies:
```bash
pip install -r requirements.txt
```
3. Run the development server:
```bash
python app.py
```

### Cloud Deployment

The application can be deployed to various cloud platforms:

- **Render**
  - Build command: `pip install -r requirements.txt`
  - Start command: `gunicorn app:app`

- **Heroku**
  - Automatically detects Python buildpack
  - Uses included `Procfile`

- **Railway**
  - Uses `requirements.txt` for dependencies
  - Start command: `gunicorn app:app`

- **AWS Lambda**
  - Can be containerized using included Dockerfile
  - Deploy using AWS SAM or Serverless Framework

Choose your preferred platform and follow their Python application deployment guidelines.

```bash
git clone https://
