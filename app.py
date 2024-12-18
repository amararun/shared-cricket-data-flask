from flask import Flask, render_template, request, send_file, jsonify
import pandas as pd
import zipfile
import tempfile
import os
import uuid
import shutil
from werkzeug.utils import secure_filename
import logging
import sys
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',
    stream=sys.stdout
)
logger = logging.getLogger("app")

app = Flask(__name__)

# Global state for tracking processes
active_processes = {}

# Configure upload folder
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'processed_files'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

def process_zip_file(file_path, process_id):
    """Process the ZIP file and return progress updates"""
    try:
        progress_info = {
            'status': 'processing',
            'progress': 0,
            'messages': [],
            'current_file': None
        }
        active_processes[process_id] = progress_info
        
        def add_message(msg):
            timestamp = datetime.now().strftime("%H:%M:%S")
            progress_info['messages'].append(f"[{timestamp}] {msg}")
        
        final_output = os.path.join(OUTPUT_FOLDER, f"processed_{process_id}_pipe.txt")

        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            # Filter files
            files_to_process = [
                f for f in zip_ref.namelist()
                if "info" not in f.lower() and "readme" not in f.lower()
            ]
            total_files = len(files_to_process)
            
            # Add initial messages
            add_message(f"Found {total_files} files to process")
            add_message(f"Using batch size of 500 files for efficient processing")
            total_batches = (total_files + 499) // 500  # Round up division
            add_message(f"Total number of batches: {total_batches}")
            
            # Process in batches
            batch_size = 500
            with tempfile.TemporaryDirectory() as temp_dir:
                for batch_start in range(0, len(files_to_process), batch_size):
                    batch_end = min(batch_start + batch_size, len(files_to_process))
                    batch_files = files_to_process[batch_start:batch_end]
                    batch_dfs = []
                    current_batch = (batch_start // batch_size) + 1

                    # Add batch start message
                    add_message(f"Starting batch {current_batch} of {total_batches} (files {batch_start + 1} to {batch_end})")

                    # Process batch
                    files_in_batch = len(batch_files)
                    files_processed_in_batch = 0
                    
                    for idx, file_name in enumerate(batch_files, start=1):
                        try:
                            # Extract and process file
                            zip_ref.extract(file_name, temp_dir)
                            file_path = os.path.join(temp_dir, file_name)
                            df = pd.read_csv(file_path)
                            batch_dfs.append(df)
                            os.remove(file_path)

                            # Update progress
                            current_file = batch_start + idx
                            progress = min(95, (current_file / total_files) * 100)
                            progress_info['progress'] = progress
                            progress_info['current_file'] = current_file
                            progress_info['total_files'] = total_files
                            
                            # Update batch progress every 100 files
                            files_processed_in_batch += 1
                            if files_processed_in_batch % 100 == 0 or files_processed_in_batch == files_in_batch:
                                add_message(
                                    f"Batch {current_batch}: Processed {files_processed_in_batch} of {files_in_batch} files"
                                )

                        except Exception as e:
                            logger.error(f"Error processing {file_name}: {str(e)}")
                            add_message(f"Error processing {file_name}: {str(e)}")

                    if batch_dfs:
                        # Add batch combining message
                        add_message(f"Combining data for batch {current_batch}...")
                        
                        # Combine and process batch
                        batch_df = pd.concat(batch_dfs, ignore_index=True)
                        
                        # Process numeric columns
                        add_message(f"Processing numeric columns for batch {current_batch}...")
                        numeric_cols = ['runs_off_bat', 'extras', 'wides', 'noballs', 'byes', 'legbyes', 'penalty']
                        for col in batch_df.columns:
                            if col in numeric_cols:
                                batch_df[col] = batch_df[col].fillna(0).astype(int)
                            else:
                                batch_df[col] = batch_df[col].fillna('')

                        # Save batch
                        add_message(f"Saving processed data for batch {current_batch}...")
                        mode = 'w' if batch_start == 0 else 'a'
                        batch_df.to_csv(
                            final_output,
                            sep='|',
                            index=False,
                            mode=mode,
                            header=(batch_start == 0)
                        )
                        
                        # Add batch completion message
                        add_message(f"✓ Completed batch {current_batch} of {total_batches}")

        # Mark as completed
        progress_info['progress'] = 100
        progress_info['status'] = 'completed'
        add_message("All batches processed successfully! You can now download the processed file.")
        return True

    except Exception as e:
        logger.error(f"Error: {str(e)}")
        progress_info['status'] = 'error'
        progress_info['error'] = str(e)
        add_message(f"Error: {str(e)}")
        return False

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/process', methods=['POST'])
def process_files():
    if 'file' not in request.files:
        return jsonify({'status': 'error', 'message': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'status': 'error', 'message': 'No file selected'}), 400
    
    if not file.filename.endswith('.zip'):
        return jsonify({'status': 'error', 'message': 'Only ZIP files are supported'}), 400

    try:
        # Save uploaded file
        process_id = str(uuid.uuid4())
        temp_path = os.path.join(UPLOAD_FOLDER, f"{process_id}_{secure_filename(file.filename)}")
        file.save(temp_path)

        # Process file in a separate thread
        from threading import Thread
        thread = Thread(target=process_zip_file, args=(temp_path, process_id))
        thread.start()

        return jsonify({
            'status': 'processing',
            'process_id': process_id
        })

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/status/<process_id>')
def get_status(process_id):
    if process_id not in active_processes:
        return jsonify({'status': 'error', 'message': 'Process not found'}), 404
    
    process_info = active_processes[process_id]
    return jsonify({
        'status': process_info['status'],
        'progress': process_info['progress'],
        'current_file': process_info.get('current_file'),
        'total_files': process_info.get('total_files'),
        'messages': process_info.get('messages', [])
    })

@app.route('/api/download/<process_id>')
def download_file(process_id):
    file_path = os.path.join(OUTPUT_FOLDER, f"processed_{process_id}_pipe.txt")
    if not os.path.exists(file_path):
        return jsonify({'status': 'error', 'message': 'File not found'}), 404
    
    return send_file(
        file_path,
        mimetype='text/plain',
        as_attachment=True,
        download_name=f"processed_data_{process_id}.txt"
    )

if __name__ == '__main__':
    # For local development
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True) 