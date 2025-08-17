#!/usr/bin/env python3
"""
Web-Based GUI for CSV Character Encoding Detection Tool
Double-click to run - opens in your browser automatically!

User Experience:
1. Double-click this file
2. Browser opens with modern interface
3. Drag and drop folders
4. See results in real-time
"""

import http.server
import socketserver
import webbrowser
import subprocess
import threading
import os
import sys
import json
import urllib.parse
from pathlib import Path
import tempfile
import time
import socket

class CharsetAnalyzerHandler(http.server.SimpleHTTPRequestHandler):
    """Custom HTTP handler for the charset analyzer web GUI"""
    
    def __init__(self, *args, **kwargs):
        # Store reference to charset script
        self.charset_script = Path(__file__).parent / "check_csv_charset.py"
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """Handle GET requests"""
        if self.path == '/' or self.path == '/index.html':
            self.serve_main_page()
        elif self.path == '/api/status':
            self.serve_status()
        else:
            super().do_GET()
    
    def do_POST(self):
        """Handle POST requests"""
        if self.path == '/api/analyze':
            self.handle_analyze()
        else:
            self.send_error(404)
    
    def serve_main_page(self):
        """Serve the main HTML interface"""
        html_content = self.get_html_interface()
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.send_header('Content-length', len(html_content.encode()))
        self.end_headers()
        self.wfile.write(html_content.encode())
    
    def serve_status(self):
        """Serve status information"""
        status = {
            'script_available': self.charset_script.exists(),
            'script_path': str(self.charset_script)
        }
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(status).encode())
    
    def handle_analyze(self):
        """Handle analysis requests"""
        try:
            # Get content length
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            # Parse JSON data
            data = json.loads(post_data.decode())
            folder_path = data.get('folder_path', '')
            mode = data.get('mode', 'analyze')
            target_encoding = data.get('target_encoding', 'utf-8')
            dry_run = data.get('dry_run', True)
            fast_mode = data.get('fast_mode', False)
            
            # Validate folder path
            if not folder_path or not os.path.exists(folder_path):
                self.send_json_response({'error': 'Invalid folder path'}, 400)
                return
            
            # Check if user provided direct CSV folder vs parent folder
            folder_path_obj = Path(folder_path)
            if not folder_path_obj.is_dir():
                self.send_json_response({'error': 'Path is not a directory'}, 400)
                return
            
            # Auto-detect folder structure (but now we support both!)
            csv_files_in_root = list(folder_path_obj.glob('*.csv')) + list(folder_path_obj.glob('*.CSV'))
            subfolders = [d for d in folder_path_obj.iterdir() if d.is_dir()]
            
            # Check if we have CSV files at all
            total_csv_in_subfolders = 0
            for subfolder in subfolders:
                subfolder_csv = list(subfolder.rglob('*.csv')) + list(subfolder.rglob('*.CSV'))
                total_csv_in_subfolders += len(subfolder_csv)
            
            if not csv_files_in_root and total_csv_in_subfolders == 0:
                self.send_json_response({
                    'error': f'No CSV files found in this directory or its subfolders.',
                    'help': 'Please select a folder that contains CSV files directly or has subfolders with CSV files.'
                }, 400)
                return
            
            if not self.charset_script.exists():
                self.send_json_response({'error': 'check_csv_charset.py not found'}, 500)
                return
            
            # Build command
            cmd = [sys.executable, str(self.charset_script), folder_path]
            
            if mode == 'convert':
                cmd.extend(['--convert-to', target_encoding])
                if dry_run:
                    cmd.append('--dry-run')
            
            if fast_mode:
                cmd.append('--fast')
            
            # Always add summary for cleaner output
            cmd.append('--summary-only')
            
            # Run analysis
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
                
                # Clean ANSI codes from output
                clean_output = self.clean_ansi_codes(result.stdout)
                
                response = {
                    'success': result.returncode == 0,
                    'output': clean_output,
                    'error_output': result.stderr if result.stderr else None,
                    'command': ' '.join(cmd[1:])  # Don't include python path
                }
                
                self.send_json_response(response)
                
            except subprocess.TimeoutExpired:
                self.send_json_response({'error': 'Analysis timed out (5 minutes)'}, 500)
            except Exception as e:
                self.send_json_response({'error': f'Analysis failed: {str(e)}'}, 500)
                
        except Exception as e:
            self.send_json_response({'error': f'Request processing failed: {str(e)}'}, 500)
    
    def send_json_response(self, data, status_code=200):
        """Send JSON response"""
        response_data = json.dumps(data).encode()
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.send_header('Content-length', len(response_data))
        self.end_headers()
        self.wfile.write(response_data)
    
    def clean_ansi_codes(self, text):
        """Remove ANSI color codes from text"""
        import re
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        return ansi_escape.sub('', text)
    
    def get_html_interface(self):
        """Generate the HTML interface"""
        return '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CSV Charset Analyzer</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 900px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        
        .header {
            background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        
        .header h1 {
            font-size: 2.5rem;
            margin-bottom: 10px;
            font-weight: 700;
        }
        
        .header p {
            opacity: 0.9;
            font-size: 1.1rem;
        }
        
        .content {
            padding: 40px;
        }
        
        .section {
            margin-bottom: 30px;
        }
        
        .section h2 {
            color: #374151;
            margin-bottom: 15px;
            font-size: 1.4rem;
            font-weight: 600;
        }
        
        .drop-zone {
            border: 3px dashed #d1d5db;
            border-radius: 12px;
            padding: 60px 20px;
            text-align: center;
            background: #f9fafb;
            transition: all 0.3s ease;
            cursor: pointer;
        }
        
        .drop-zone:hover, .drop-zone.dragover {
            border-color: #4f46e5;
            background: #eef2ff;
        }
        
        .drop-zone.selected {
            border-color: #10b981;
            background: #d1fae5;
            border-style: solid;
        }
        
        .drop-zone-content {
            pointer-events: none;
        }
        
        .drop-zone h3 {
            color: #6b7280;
            font-size: 1.3rem;
            margin-bottom: 10px;
        }
        
        .drop-zone p {
            color: #9ca3af;
            font-size: 1rem;
        }
        
        .folder-info {
            background: #e5e7eb;
            padding: 15px;
            border-radius: 8px;
            margin: 15px 0;
            display: none;
        }
        
        .folder-info.show {
            display: block;
        }
        
        .info-box {
            background: #eff6ff;
            border: 1px solid #bfdbfe;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
        }
        
        .info-box h4 {
            color: #1e40af;
            margin-bottom: 15px;
            font-size: 1.1rem;
        }
        
        .folder-structure {
            background: #f8fafc;
            padding: 15px;
            border-radius: 6px;
            font-family: 'SF Mono', Monaco, 'Cascadia Code', 'Roboto Mono', Consolas, 'Courier New', monospace;
            font-size: 0.9rem;
            line-height: 1.6;
            margin-bottom: 15px;
            border-left: 4px solid #3b82f6;
        }
        
        .info-box p {
            color: #374151;
            margin: 0;
            line-height: 1.5;
        }
        
        .options {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin: 30px 0;
        }
        
        .option-group {
            background: #f9fafb;
            padding: 20px;
            border-radius: 12px;
            border: 1px solid #e5e7eb;
        }
        
        .option-group h3 {
            color: #374151;
            margin-bottom: 15px;
            font-size: 1.1rem;
        }
        
        .radio-group {
            margin-bottom: 15px;
        }
        
        .radio-item {
            display: flex;
            align-items: center;
            margin-bottom: 10px;
        }
        
        .radio-item input[type="radio"] {
            margin-right: 10px;
        }
        
        .checkbox-item {
            display: flex;
            align-items: center;
            margin-bottom: 10px;
        }
        
        .checkbox-item input[type="checkbox"] {
            margin-right: 10px;
        }
        
        select {
            width: 100%;
            padding: 8px 12px;
            border: 1px solid #d1d5db;
            border-radius: 6px;
            margin-top: 5px;
        }
        
        .action-buttons {
            display: flex;
            gap: 15px;
            justify-content: center;
            margin: 30px 0;
        }
        
        .btn {
            padding: 12px 24px;
            border: none;
            border-radius: 8px;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            text-decoration: none;
            display: inline-flex;
            align-items: center;
            gap: 8px;
        }
        
        .btn-primary {
            background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
            color: white;
        }
        
        .btn-primary:hover:not(:disabled) {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(79, 70, 229, 0.3);
        }
        
        .btn-secondary {
            background: #f3f4f6;
            color: #374151;
            border: 1px solid #d1d5db;
        }
        
        .btn-secondary:hover {
            background: #e5e7eb;
        }
        
        .btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
        }
        
        .status {
            text-align: center;
            margin: 20px 0;
            padding: 15px;
            border-radius: 8px;
            display: none;
        }
        
        .status.show {
            display: block;
        }
        
        .status.success {
            background: #d1fae5;
            color: #065f46;
            border: 1px solid #a7f3d0;
        }
        
        .status.error {
            background: #fee2e2;
            color: #991b1b;
            border: 1px solid #fca5a5;
        }
        
        .status.info {
            background: #dbeafe;
            color: #1e40af;
            border: 1px solid #93c5fd;
        }
        
        .progress {
            width: 100%;
            height: 6px;
            background: #e5e7eb;
            border-radius: 3px;
            overflow: hidden;
            margin: 20px 0;
            display: none;
        }
        
        .progress.show {
            display: block;
        }
        
        .progress-bar {
            height: 100%;
            background: linear-gradient(90deg, #4f46e5, #7c3aed);
            animation: progress 2s infinite;
        }
        
        @keyframes progress {
            0% { transform: translateX(-100%); }
            100% { transform: translateX(100%); }
        }
        
        .output {
            background: #1f2937;
            color: #e5e7eb;
            padding: 20px;
            border-radius: 8px;
            font-family: 'SF Mono', Monaco, 'Cascadia Code', 'Roboto Mono', Consolas, 'Courier New', monospace;
            font-size: 0.9rem;
            line-height: 1.6;
            white-space: pre-wrap;
            max-height: 400px;
            overflow-y: auto;
            margin: 20px 0;
            display: none;
        }
        
        .output.show {
            display: block;
        }
        
        .convert-options {
            opacity: 0.5;
            pointer-events: none;
            transition: all 0.3s ease;
        }
        
        .convert-options.enabled {
            opacity: 1;
            pointer-events: auto;
        }
        
        @media (max-width: 768px) {
            .options {
                grid-template-columns: 1fr;
            }
            
            .action-buttons {
                flex-direction: column;
            }
            
            .header h1 {
                font-size: 2rem;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔍 CSV Charset Analyzer</h1>
            <p>Easy drag-and-drop character encoding analysis</p>
        </div>
        
        <div class="content">
            <div class="section">
                <h2>📁 Select Your CSV Folder</h2>
                <div class="info-box">
                    <h4>📖 Supported Folder Structures:</h4>
                    <div class="folder-structure">
                        <div><strong>Option 1: Direct CSV Folder</strong></div>
                        <div>📁 <strong>csv_folder/</strong> ← Select this</div>
                        <div>&nbsp;&nbsp;&nbsp;&nbsp;📄 file1.csv</div>
                        <div>&nbsp;&nbsp;&nbsp;&nbsp;📄 file2.csv</div>
                        <div>&nbsp;&nbsp;&nbsp;&nbsp;📄 data.csv</div>
                        <div></div>
                        <div><strong>Option 2: Parent with Subfolders</strong></div>
                        <div>📁 <strong>parent_folder/</strong> ← Select this</div>
                        <div>&nbsp;&nbsp;&nbsp;&nbsp;📁 subfolder1/</div>
                        <div>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;📄 file1.csv</div>
                        <div>&nbsp;&nbsp;&nbsp;&nbsp;📁 subfolder2/</div>
                        <div>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;📄 data.csv</div>
                    </div>
                    <p><strong>Flexible:</strong> The tool automatically detects which structure you're using!</p>
                </div>
                <div class="drop-zone" id="dropZone">
                    <div class="drop-zone-content">
                        <h3>📂 Click to select your CSV folder</h3>
                        <p>Choose the folder containing your CSV files</p>
                        <small style="color: #9ca3af; margin-top: 8px; display: block;">
                            Modern browsers (Chrome/Edge) will show a folder picker.<br>
                            Other browsers will show a path input dialog.
                        </small>
                    </div>
                </div>
                <div class="folder-info" id="folderInfo">
                    <strong>Selected folder:</strong> <span id="folderPath"></span>
                </div>
            </div>
            
            <div class="section">
                <h2>⚙️ Analysis Options</h2>
                <div class="options">
                    <div class="option-group">
                        <h3>What would you like to do?</h3>
                        <div class="radio-group">
                            <div class="radio-item">
                                <input type="radio" id="modeAnalyze" name="mode" value="analyze" checked>
                                <label for="modeAnalyze">🔍 Analyze encodings only (safe)</label>
                            </div>
                            <div class="radio-item">
                                <input type="radio" id="modeConvert" name="mode" value="convert">
                                <label for="modeConvert">🔄 Convert files to standard encoding</label>
                            </div>
                        </div>
                        
                        <div class="convert-options" id="convertOptions">
                            <label for="targetEncoding">Target encoding:</label>
                            <select id="targetEncoding">
                                <option value="utf-8">UTF-8 (recommended)</option>
                                <option value="utf-8-sig">UTF-8 with BOM</option>
                                <option value="ascii">ASCII</option>
                                <option value="iso-8859-1">ISO-8859-1</option>
                                <option value="windows-1252">Windows-1252</option>
                            </select>
                            
                            <div class="checkbox-item" style="margin-top: 15px;">
                                <input type="checkbox" id="dryRun" checked>
                                <label for="dryRun">Preview only (recommended)</label>
                            </div>
                        </div>
                    </div>
                    
                    <div class="option-group">
                        <h3>Advanced Options</h3>
                        <div class="checkbox-item">
                            <input type="checkbox" id="fastMode">
                            <label for="fastMode">⚡ Fast mode (quicker, slightly less accurate)</label>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="action-buttons">
                <button class="btn btn-primary" id="analyzeBtn" disabled>
                    🚀 Start Analysis
                </button>
                <button class="btn btn-secondary" id="clearBtn">
                    🗑️ Clear Output
                </button>
            </div>
            
            <div class="status" id="status"></div>
            <div class="progress" id="progress">
                <div class="progress-bar"></div>
            </div>
            <div class="output" id="output"></div>
        </div>
    </div>

    <script>
        let selectedFolder = null;
        
        // DOM elements
        const dropZone = document.getElementById('dropZone');
        const folderInfo = document.getElementById('folderInfo');
        const folderPath = document.getElementById('folderPath');
        const analyzeBtn = document.getElementById('analyzeBtn');
        const clearBtn = document.getElementById('clearBtn');
        const status = document.getElementById('status');
        const progress = document.getElementById('progress');
        const output = document.getElementById('output');
        const modeAnalyze = document.getElementById('modeAnalyze');
        const modeConvert = document.getElementById('modeConvert');
        const convertOptions = document.getElementById('convertOptions');
        
        // Mode change handler
        function updateModeOptions() {
            if (modeConvert.checked) {
                convertOptions.classList.add('enabled');
            } else {
                convertOptions.classList.remove('enabled');
            }
        }
        
        modeAnalyze.addEventListener('change', updateModeOptions);
        modeConvert.addEventListener('change', updateModeOptions);
        
        // Folder selection handlers
        dropZone.addEventListener('click', async () => {
            try {
                // Try modern Directory Picker API first (Chrome/Edge)
                if ('showDirectoryPicker' in window) {
                    try {
                        const dirHandle = await window.showDirectoryPicker();
                        selectFolder(dirHandle.name); // Note: We can't get full path for security
                        showStatus('Folder selected! Note: For security reasons, browser shows folder name only.', 'info');
                    } catch (err) {
                        if (err.name !== 'AbortError') {
                            console.error('Directory picker error:', err);
                            fallbackFolderInput();
                        }
                    }
                } else {
                    // Fallback for other browsers
                    fallbackFolderInput();
                }
            } catch (error) {
                console.error('Folder selection error:', error);
                fallbackFolderInput();
            }
        });
        
        function fallbackFolderInput() {
            showFolderInputDialog();
        }
        
        function showFolderInputDialog() {
            // Create a more user-friendly input dialog
            const modal = document.createElement('div');
            modal.style.cssText = `
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0,0,0,0.5);
                display: flex;
                align-items: center;
                justify-content: center;
                z-index: 1000;
            `;
            
            const dialog = document.createElement('div');
            dialog.style.cssText = `
                background: white;
                padding: 30px;
                border-radius: 12px;
                box-shadow: 0 20px 40px rgba(0,0,0,0.3);
                max-width: 500px;
                width: 90%;
            `;
            
            dialog.innerHTML = `
                <h3 style="margin: 0 0 20px 0; color: #374151; font-size: 1.4rem;">📁 Select Your CSV Folder</h3>
                <p style="margin: 0 0 20px 0; color: #6b7280; line-height: 1.5;">
                    Enter the full path to your folder containing CSV files. You can:
                </p>
                <ul style="margin: 0 0 20px 20px; color: #6b7280; line-height: 1.6;">
                    <li>Copy the path from your file manager</li>
                    <li>Right-click a folder → "Copy path" (Windows)</li>
                    <li>Right-click a folder → "Get Info" (macOS)</li>
                </ul>
                <input 
                    type="text" 
                    id="folderPathInput" 
                    placeholder="e.g., /Users/username/Documents/csv_files"
                    style="
                        width: 100%;
                        padding: 12px;
                        border: 2px solid #d1d5db;
                        border-radius: 6px;
                        font-size: 14px;
                        margin-bottom: 20px;
                        box-sizing: border-box;
                    "
                />
                <div style="display: flex; gap: 10px; justify-content: flex-end;">
                    <button 
                        id="cancelBtn"
                        style="
                            padding: 10px 20px;
                            border: 1px solid #d1d5db;
                            background: #f9fafb;
                            color: #374151;
                            border-radius: 6px;
                            cursor: pointer;
                        "
                    >
                        Cancel
                    </button>
                    <button 
                        id="selectBtn"
                        style="
                            padding: 10px 20px;
                            border: none;
                            background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
                            color: white;
                            border-radius: 6px;
                            cursor: pointer;
                        "
                    >
                        Select Folder
                    </button>
                </div>
            `;
            
            modal.appendChild(dialog);
            document.body.appendChild(modal);
            
            const input = document.getElementById('folderPathInput');
            const selectBtn = document.getElementById('selectBtn');
            const cancelBtn = document.getElementById('cancelBtn');
            
            // Focus the input
            input.focus();
            
            // Handle buttons
            selectBtn.addEventListener('click', () => {
                const path = input.value.trim();
                if (path) {
                    selectFolder(path);
                    document.body.removeChild(modal);
                } else {
                    input.style.borderColor = '#ef4444';
                    input.focus();
                }
            });
            
            cancelBtn.addEventListener('click', () => {
                document.body.removeChild(modal);
            });
            
            // Handle Enter key
            input.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    selectBtn.click();
                }
            });
            
            // Handle Escape key
            document.addEventListener('keydown', function escapeHandler(e) {
                if (e.key === 'Escape') {
                    document.body.removeChild(modal);
                    document.removeEventListener('keydown', escapeHandler);
                }
            });
            
            // Close on backdrop click
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    document.body.removeChild(modal);
                }
            });
        }
        
        // Drag and drop handlers
        dropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            dropZone.classList.add('dragover');
        });
        
        dropZone.addEventListener('dragleave', () => {
            dropZone.classList.remove('dragover');
        });
        
        dropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            dropZone.classList.remove('dragover');
            
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                // Note: Web browsers can't access full file paths for security
                // This is a limitation we need to work around
                showStatus('Due to browser security, drag & drop only shows filenames. Please click to select folder properly.', 'info');
                // Open the folder picker dialog
                showFolderInputDialog();
            }
        });
        
        function selectFolder(path) {
            selectedFolder = path;
            folderPath.textContent = path;
            folderInfo.classList.add('show');
            dropZone.classList.add('selected');
            analyzeBtn.disabled = false;
            showStatus('Folder selected! Ready to analyze.', 'success');
        }
        
        // Analysis handler
        analyzeBtn.addEventListener('click', async () => {
            if (!selectedFolder) {
                showStatus('Please select a folder first!', 'error');
                return;
            }
            
            const analysisData = {
                folder_path: selectedFolder,
                mode: document.querySelector('input[name="mode"]:checked').value,
                target_encoding: document.getElementById('targetEncoding').value,
                dry_run: document.getElementById('dryRun').checked,
                fast_mode: document.getElementById('fastMode').checked
            };
            
            try {
                analyzeBtn.disabled = true;
                showStatus('Running analysis...', 'info');
                showProgress(true);
                
                const response = await fetch('/api/analyze', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(analysisData)
                });
                
                const result = await response.json();
                
                if (result.success) {
                    showStatus('Analysis completed successfully!', 'success');
                    showOutput(result.output);
                } else {
                    // Check if there's a suggestion for better path
                    if (result.suggestion) {
                        const message = `${result.error}\\n\\n💡 Suggestion: ${result.suggestion}\\n\\nℹ️ ${result.help}`;
                        showStatus('Folder structure issue detected', 'error');
                        showOutput(message);
                        
                        // Ask if user wants to try the suggested path
                        const tryAgain = confirm(`Found issue with folder structure.\\n\\n${result.help}\\n\\nWould you like to try the suggested path instead?\\n${result.suggestion}`);
                        if (tryAgain) {
                            selectFolder(result.suggestion);
                            return;
                        }
                    } else {
                        showStatus('Analysis failed. See output for details.', 'error');
                        showOutput(result.error_output || result.error || 'Unknown error');
                    }
                }
                
            } catch (error) {
                showStatus(`Network error: ${error.message}`, 'error');
            } finally {
                analyzeBtn.disabled = false;
                showProgress(false);
            }
        });
        
        // Clear output handler
        clearBtn.addEventListener('click', () => {
            output.textContent = '';
            output.classList.remove('show');
            hideStatus();
        });
        
        // Utility functions
        function showStatus(message, type) {
            status.textContent = message;
            status.className = `status show ${type}`;
        }
        
        function hideStatus() {
            status.classList.remove('show');
        }
        
        function showProgress(show) {
            if (show) {
                progress.classList.add('show');
            } else {
                progress.classList.remove('show');
            }
        }
        
        function showOutput(text) {
            output.textContent = text;
            output.classList.add('show');
            output.scrollTop = output.scrollHeight;
        }
        
        // Initialize
        updateModeOptions();
        
        // Check if charset script is available
        fetch('/api/status')
            .then(response => response.json())
            .then(data => {
                if (!data.script_available) {
                    showStatus('Warning: check_csv_charset.py not found in the same directory!', 'error');
                }
            })
            .catch(error => {
                console.error('Status check failed:', error);
            });
    </script>
</body>
</html>'''

def find_free_port():
    """Find a free port to run the server on"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        s.listen(1)
        port = s.getsockname()[1]
    return port

def main():
    """Main function to start the web server"""
    # Check if charset script exists
    script_dir = Path(__file__).parent
    charset_script = script_dir / "check_csv_charset.py"
    
    if not charset_script.exists():
        print("❌ Error: check_csv_charset.py not found!")
        print(f"Please make sure check_csv_charset.py is in the same folder as this script.")
        print(f"Looking for: {charset_script}")
        input("Press Enter to exit...")
        return
    
    # Find a free port
    port = find_free_port()
    
    print(f"🚀 Starting CSV Charset Analyzer...")
    print(f"📁 Script location: {script_dir}")
    print(f"🌐 Starting web server on port {port}...")
    
    try:
        # Start server
        with socketserver.TCPServer(("", port), CharsetAnalyzerHandler) as httpd:
            server_url = f"http://localhost:{port}"
            
            print(f"✅ Server started successfully!")
            print(f"🔗 Opening browser: {server_url}")
            print(f"")
            print(f"💡 Instructions:")
            print(f"   1. A browser window should open automatically")
            print(f"   2. If not, manually open: {server_url}")
            print(f"   3. Drag and drop or enter your CSV folder path")
            print(f"   4. Click 'Start Analysis' to run")
            print(f"")
            print(f"⏹️  To stop: Press Ctrl+C in this window")
            print(f"{'='*60}")
            
            # Open browser automatically
            def open_browser():
                time.sleep(1)  # Give server time to start
                try:
                    webbrowser.open(server_url)
                except Exception as e:
                    print(f"Could not auto-open browser: {e}")
                    print(f"Please manually open: {server_url}")
            
            browser_thread = threading.Thread(target=open_browser)
            browser_thread.daemon = True
            browser_thread.start()
            
            # Serve forever
            httpd.serve_forever()
            
    except KeyboardInterrupt:
        print(f"\\n⏹️  Server stopped by user")
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        input("Press Enter to exit...")

if __name__ == "__main__":
    main()