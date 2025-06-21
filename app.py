from flask import Flask, render_template, request, jsonify, flash, redirect, url_for
import os
import pandas as pd
from werkzeug.utils import secure_filename
import json
from mindsdb_handler import MindsDBHandler
import logging
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'dev-key-change-in-production')
app.config['UPLOAD_FOLDER'] = os.getenv('UPLOAD_FOLDER', 'uploads')
app.config['MAX_CONTENT_LENGTH'] = int(os.getenv('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))  # 16MB default

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize MindsDB handler
mindsdb_handler = MindsDBHandler()

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('index.html')

@app.route('/search')
def search_page():
    """Search interface page"""
    return render_template('search.html')

@app.route('/upload')
def upload_page():
    """File upload page"""
    return render_template('upload.html')

@app.route('/agent')
def agent_page():
    """AI Agent interaction page"""
    return render_template('agent.html')

@app.route('/jobs')
def jobs_page():
    """Jobs management page"""
    return render_template('jobs.html')

@app.route('/api/search', methods=['POST'])
def api_search():
    """API endpoint for semantic search"""
    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        category = data.get('category', '').strip()
        limit = data.get('limit', 5)
        
        if not query:
            return jsonify({'error': 'Query is required'}), 400
        
        # Perform semantic search
        results = mindsdb_handler.semantic_search(query, category, limit)
        
        # Get the last executed query for transparency
        last_queries = mindsdb_handler.get_last_queries(1)
        
        return jsonify({
            'success': True,
            'results': results,
            'query': query,
            'category': category if category else 'All Categories',
            'executed_query': last_queries[0] if last_queries else None
        })
        
    except Exception as e:
        logger.error(f"Search API error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/agent', methods=['POST'])
def api_agent():
    """API endpoint for AI agent queries"""
    try:
        data = request.get_json()
        question = data.get('question', '').strip()
        
        if not question:
            return jsonify({'error': 'Question is required'}), 400
          # Get AI agent response
        response = mindsdb_handler.ask_agent(question)
        
        # Get the last executed query for transparency
        last_queries = mindsdb_handler.get_last_queries(1)
        
        return jsonify({
            'success': True,
            'answer': response,
            'question': question,
            'executed_query': last_queries[0] if last_queries else None
        })
        
    except Exception as e:
        logger.error(f"Agent API error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/upload', methods=['POST'])
def api_upload():
    """API endpoint for file upload"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file selected'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not file.filename.endswith('.csv'):
            return jsonify({'error': 'Only CSV files are allowed'}), 400
        
        # Save uploaded file
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Process CSV and insert into knowledge base
        try:
            df = pd.read_csv(filepath)
            
            # Validate CSV structure
            required_columns = ['doc_id', 'title', 'category', 'content']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                os.remove(filepath)  # Clean up
                return jsonify({
                    'error': f'CSV missing required columns: {", ".join(missing_columns)}'
                }), 400
              # Insert data into knowledge base
            inserted_count = mindsdb_handler.insert_documents(df)
            
            # Get sample queries for transparency
            sample_queries = mindsdb_handler.get_last_queries(3)
            
            # Clean up uploaded file
            os.remove(filepath)
            
            return jsonify({
                'success': True,
                'message': f'Successfully inserted {inserted_count} documents into knowledge base',
                'inserted_count': inserted_count,
                'sample_queries': sample_queries
            })
            
        except Exception as e:
            # Clean up on error
            if os.path.exists(filepath):
                os.remove(filepath)
            raise e
        
    except Exception as e:
        logger.error(f"Upload API error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/status')
def api_status():
    """API endpoint to check system status"""
    try:
        status = mindsdb_handler.check_status()
        return jsonify(status)
    except Exception as e:
        logger.error(f"Status API error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/categories')
def api_categories():
    """API endpoint to get available categories"""
    try:
        categories = mindsdb_handler.get_categories()
        return jsonify({
            'success': True,
            'categories': categories
        })
    except Exception as e:
        logger.error(f"Categories API error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/initialize', methods=['POST'])
def api_initialize():
    """API endpoint to initialize knowledge base and agent"""
    try:
        result = mindsdb_handler.initialize_system()
        return jsonify(result)
    except Exception as e:
        logger.error(f"Initialize API error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/jobs', methods=['GET'])
def api_get_jobs():
    """API endpoint to get list of jobs"""
    try:
        jobs = mindsdb_handler.list_jobs()
        return jsonify({'success': True, 'jobs': jobs})
    except Exception as e:
        logger.error(f"Get jobs API error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/jobs', methods=['POST'])
def api_create_job():
    """API endpoint to create a new job"""
    try:
        data = request.get_json()
        job_name = data.get('name', '').strip()
        job_type = data.get('type', '').strip()
        schedule = data.get('schedule', '').strip()
        custom_query = data.get('custom_query', '').strip()
        
        if not job_name or not job_type or not schedule:
            return jsonify({'error': 'Name, type, and schedule are required'}), 400
        
        if job_type == 'custom' and not custom_query:
            return jsonify({'error': 'Custom query is required for custom job type'}), 400
        
        # Create the job
        result = mindsdb_handler.create_job(job_name, job_type, schedule, custom_query)
        
        if result['success']:
            # Get the last executed query for transparency
            last_queries = mindsdb_handler.get_last_queries(1)
            
            return jsonify({
                'success': True,
                'message': result['message'],
                'job': {
                    'id': f'job_{int(time.time())}',
                    'name': job_name,
                    'type': job_type,
                    'status': 'created',
                    'schedule': schedule,
                    'created_at': time.strftime('%Y-%m-%d %H:%M:%S'),
                    'query': result.get('query', ''),
                    'custom_query': custom_query if custom_query else None
                },
                'executed_query': last_queries[0] if last_queries else None
            })
        else:
            return jsonify(result), 400
        
    except Exception as e:
        logger.error(f"Create job API error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/jobs/<job_id>', methods=['DELETE'])
def api_delete_job(job_id):
    """API endpoint to stop/delete a job"""
    try:
        # Extract job name from job_id (assuming format job_name or similar)
        job_name = job_id.replace('job_', '') if job_id.startswith('job_') else job_id
        
        result = mindsdb_handler.stop_job(job_name)
        
        if result['success']:
            # Get the last executed query for transparency
            last_queries = mindsdb_handler.get_last_queries(1)
            
            return jsonify({
                'success': True,
                'message': result['message'],
                'executed_query': last_queries[0] if last_queries else None
            })
        else:
            return jsonify(result), 400
        
    except Exception as e:
        logger.error(f"Delete job API error: {e}")
        return jsonify({'error': str(e)}), 500

@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

if __name__ == '__main__':
    # Get configuration from environment variables
    debug_mode = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_PORT', 5000))
    
    app.run(debug=debug_mode, host=host, port=port)
