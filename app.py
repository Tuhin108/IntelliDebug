from flask import Flask, render_template, request, jsonify
import sys
import io
import contextlib
import traceback
import re
import subprocess
import tempfile
import os
from flask_cors import CORS
import logging
from datetime import datetime

app = Flask(__name__)
CORS(app)

# ✅ Configure UTF-8 compatible logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

log_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# File handler with UTF-8
file_handler = logging.FileHandler('debugger.log', encoding='utf-8')
file_handler.setFormatter(log_formatter)
logger.addHandler(file_handler)

# Stream (console) handler with UTF-8
stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setFormatter(log_formatter)
logger.addHandler(stream_handler)

# Configure Gemini AI (optional - will work without it)
model = None
try:
    import google.generativeai as genai
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    if GEMINI_API_KEY:
        try:
            genai.configure(api_key=GEMINI_API_KEY)
            model = genai.GenerativeModel('gemini-2.0-flash-exp')
            logger.info("✅ Gemini AI configured and ready")
        except Exception as e:
            logger.error(f"Failed to configure Gemini AI: {e}")
            model = None
    else:
        logger.warning("⚠️ Warning: GEMINI_API_KEY not set. AI explanations will be unavailable")
except ImportError:
    logger.warning("⚠️ Google Generative AI not installed. AI explanations will be unavailable")
    logger.info("Install with: pip install google-generativeai")

class PythonDebugger:
    def __init__(self):
        self.max_execution_time = 5  # seconds
        self.max_output_length = 2000
    
    def safe_execute(self, code):
        """Safely execute Python code and capture output/errors"""
        if not code or not code.strip():
            return {
                'success': False,
                'output': '',
                'error': 'No code provided',
                'return_code': -1
            }
        
        # Create a temporary file to execute the code
        temp_file = None
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
                f.write(code)
                temp_file = f.name
            
            logger.info(f"Executing code in temporary file: {temp_file}")
            
            # Execute the code in a subprocess with timeout
            result = subprocess.run(
                [sys.executable, temp_file],
                capture_output=True,
                text=True,
                timeout=self.max_execution_time,
                encoding='utf-8'
            )
            
            output = result.stdout or ''
            error = result.stderr or ''
            
            # Limit output length
            if len(output) > self.max_output_length:
                output = output[:self.max_output_length] + "\n... (output truncated)"
            
            logger.info(f"Code execution completed with return code: {result.returncode}")
            
            return {
                'success': result.returncode == 0,
                'output': output,
                'error': error,
                'return_code': result.returncode
            }
        
        except subprocess.TimeoutExpired:
            logger.warning("Code execution timed out")
            return {
                'success': False,
                'output': '',
                'error': f'Code execution timed out (>{self.max_execution_time} seconds). Possible infinite loop?',
                'return_code': -1
            }
        except Exception as e:
            logger.error(f"Execution error: {e}")
            return {
                'success': False,
                'output': '',
                'error': f'Execution error: {str(e)}',
                'return_code': -1
            }
        finally:
            # Clean up temporary file
            if temp_file:
                try:
                    os.unlink(temp_file)
                    logger.debug(f"Cleaned up temporary file: {temp_file}")
                except Exception as e:
                    logger.warning(f"Failed to clean up temporary file {temp_file}: {e}")
    
    def analyze_syntax(self, code):
        """Check for syntax errors without executing"""
        try:
            compile(code, '<string>', 'exec')
            return None
        except SyntaxError as e:
            return {
                'type': 'SyntaxError',
                'message': str(e),
                'line': e.lineno,
                'offset': e.offset
            }
        except Exception as e:
            return {
                'type': type(e).__name__,
                'message': str(e),
                'line': None,
                'offset': None
            }
    
    def get_ai_explanation(self, code, error_info):
        """Get AI explanation of the error and suggested fix"""
        if not model:
            logger.warning("AI explanation requested but Gemini model not available")
            return {
                'explanation': 'AI explanation unavailable - please set GEMINI_API_KEY environment variable',
                'suggested_fix': None,
                'fix_explanation': None
            }
        
        try:
            logger.info("Requesting AI analysis from Gemini")
            
            prompt = f"""
You are a helpful Python tutor for students. Analyze this buggy Python code and error:

CODE:
```python
{code}
```

ERROR:
{error_info.get('error', 'No error message')}

Please provide:
1. A simple, student-friendly explanation of what went wrong
2. A corrected version of the code (if possible)
3. An explanation of what was changed and why

Keep explanations clear and educational. Focus on helping students learn.
Format your response as:
EXPLANATION: [simple explanation]
FIXED_CODE: [corrected code or "No fix available"]
CHANGES: [what was changed and why]
"""
            
            response = model.generate_content(prompt)
            ai_response = response.text
            
            logger.info("AI analysis completed successfully")
            
            # Parse the AI response
            explanation_match = re.search(r'EXPLANATION:\s*(.*?)(?=FIXED_CODE:|$)', ai_response, re.DOTALL)
            fix_match = re.search(r'FIXED_CODE:\s*(.*?)(?=CHANGES:|$)', ai_response, re.DOTALL)
            changes_match = re.search(r'CHANGES:\s*(.*)', ai_response, re.DOTALL)
            
            explanation = explanation_match.group(1).strip() if explanation_match else "Unable to analyze the error."
            suggested_fix = fix_match.group(1).strip() if fix_match else None
            fix_explanation = changes_match.group(1).strip() if changes_match else None
            
            # Clean up the suggested fix
            if suggested_fix and suggested_fix != "No fix available":
                suggested_fix = re.sub(r'^```python\s*', '', suggested_fix)
                suggested_fix = re.sub(r'\s*```$', '', suggested_fix)
            else:
                suggested_fix = None
            
            return {
                'explanation': explanation,
                'suggested_fix': suggested_fix,
                'fix_explanation': fix_explanation
            }
        
        except Exception as e:
            logger.error(f"AI analysis failed: {e}")
            return {
                'explanation': f'AI analysis temporarily unavailable. Error details: {error_info.get("error", "Unknown error")}',
                'suggested_fix': None,
                'fix_explanation': None
            }

debugger = PythonDebugger()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/debug', methods=['POST'])
def debug_code():
    request_id = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    logger.info(f"[{request_id}] Debug request received")
    
    try:
        # Validate request
        if not request.is_json:
            logger.warning(f"[{request_id}] Invalid request - not JSON")
            return jsonify({'error': 'Request must be JSON'}), 400
            
        data = request.get_json()
        if not data:
            logger.warning(f"[{request_id}] Invalid request - no JSON data")
            return jsonify({'error': 'No JSON data provided'}), 400
            
        code = data.get('code', '').strip()
        
        if not code:
            logger.warning(f"[{request_id}] No code provided")
            return jsonify({'error': 'No code provided'}), 400
        
        logger.info(f"[{request_id}] Processing code of length: {len(code)}")
        
        # First, check for syntax errors
        syntax_error = debugger.analyze_syntax(code)
        
        if syntax_error:
            logger.info(f"[{request_id}] Syntax error detected: {syntax_error['type']}")
            # Handle syntax errors
            error_info = {
                'error': f"{syntax_error['type']}: {syntax_error['message']}",
                'line': syntax_error.get('line'),
                'type': 'syntax'
            }
            
            ai_analysis = debugger.get_ai_explanation(code, error_info)
            
            response_data = {
                'success': False,
                'output': '',
                'error': error_info['error'],
                'error_type': 'syntax',
                'line_number': error_info['line'],
                'ai_explanation': ai_analysis['explanation'],
                'suggested_fix': ai_analysis['suggested_fix'],
                'fix_explanation': ai_analysis['fix_explanation']
            }
            
            logger.info(f"[{request_id}] Returning syntax error response")
            return jsonify(response_data)
        
        # Execute the code
        logger.info(f"[{request_id}] Executing code")
        result = debugger.safe_execute(code)
        
        if result['success']:
            logger.info(f"[{request_id}] Code executed successfully")
            response_data = {
                'success': True,
                'output': result['output'],
                'error': None,
                'ai_explanation': 'Code executed successfully! 🎉',
                'suggested_fix': None,
                'fix_explanation': None
            }
            return jsonify(response_data)
        else:
            logger.info(f"[{request_id}] Runtime error occurred")
            # Handle runtime errors
            error_info = {
                'error': result['error'],
                'type': 'runtime'
            }
            
            ai_analysis = debugger.get_ai_explanation(code, error_info)
            
            response_data = {
                'success': False,
                'output': result['output'],
                'error': result['error'],
                'error_type': 'runtime',
                'ai_explanation': ai_analysis['explanation'],
                'suggested_fix': ai_analysis['suggested_fix'],
                'fix_explanation': ai_analysis['fix_explanation']
            }
            
            logger.info(f"[{request_id}] Returning runtime error response")
            return jsonify(response_data)
    
    except Exception as e:
        logger.error(f"[{request_id}] Unexpected server error: {str(e)}")
        logger.error(f"[{request_id}] Traceback: {traceback.format_exc()}")
        return jsonify({
            'error': 'An unexpected error occurred. Please try again.',
            'debug_info': str(e) if app.debug else None
        }), 500

@app.route('/health')
def health_check():
    return jsonify({
        'status': 'healthy',
        'ai_available': bool(model),
        'timestamp': datetime.now().isoformat()
    })

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({'error': 'Method not allowed'}), 405

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {error}")
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    logger.info("Starting AI Python Debugger server...")
    
    if not model:
        logger.warning("⚠️ Warning: GEMINI_API_KEY not set. AI explanations will be unavailable.")
        logger.info("   Get your API key from: https://makersuite.google.com/app/apikey")
    else:
        logger.info("✅ Gemini AI configured and ready")
    
    # 🔧 LOCAL SERVER CONFIGURATION
    # Set default local development settings
    DEFAULT_HOST = '127.0.0.1'  # localhost only for security
    DEFAULT_PORT = 5000         # standard Flask development port
    
    # Allow override via environment variables
    host = os.environ.get('HOST', DEFAULT_HOST)
    port_str = os.environ.get('PORT', str(DEFAULT_PORT))
    
    try:
        port = int(port_str)
        # Validate port range
        if port < 1024 or port > 65535:
            logger.warning(f"⚠️ Port {port} may require admin privileges or is invalid. Consider using a port > 1024.")
    except (ValueError, TypeError):
        logger.warning(f"⚠️ Invalid PORT environment variable '{port_str}'. Using default port {DEFAULT_PORT}.")
        port = DEFAULT_PORT
    
    # Validate host for local development
    if host not in ['127.0.0.1', 'localhost', '0.0.0.0']:
        logger.warning(f"⚠️ Host '{host}' may not be suitable for local development. Consider '127.0.0.1' or 'localhost'.")
    
    logger.info("🖥️ LOCAL SERVER CONFIGURATION:")
    logger.info(f"  - Host: {host}")
    logger.info(f"  - Port: {port}")
    logger.info(f"  - Local URL: http://{host}:{port}")
    if host == '127.0.0.1':
        logger.info(f"  - Alternative URL: http://localhost:{port}")
    logger.info(f"  - Mode: Local Development")
    
    # Enable debug mode for local development
    debug_mode = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
    
    logger.info(f"  - Debug Mode: {debug_mode}")
    logger.info("🚀 Starting local Flask development server...")
    
    try:
        app.run(
            debug=debug_mode,
            host=host,
            port=port,
            use_reloader=debug_mode,  # Auto-reload on code changes in debug mode
            threaded=True             # Handle multiple requests concurrently
        )
    except OSError as e:
        if "Address already in use" in str(e):
            logger.error(f"❌ Port {port} is already in use!")
            logger.info("Try one of these solutions:")
            logger.info(f"  1. Use a different port: python app.py (set PORT environment variable)")
            logger.info(f"  2. Kill the process using port {port}")
            logger.info(f"  3. Wait a moment and try again")
        else:
            logger.error(f"❌ Failed to start server: {e}")
    except KeyboardInterrupt:
        logger.info("🛑 Server stopped by user")
    except Exception as e:
        logger.error(f"❌ Unexpected error starting server: {e}")