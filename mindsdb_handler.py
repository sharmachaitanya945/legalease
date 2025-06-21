import mindsdb_sdk
import pandas as pd
import time
from functools import wraps
import requests
import logging
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

def retry_on_error(max_retries=3, delay=2, backoff=2):
    """Decorator to retry function calls when errors occur"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            while retries < max_retries:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    error_msg = str(e).lower()
                    if ('litellm' in error_msg or 
                        'event loop is closed' in error_msg or 
                        'apiconnectionerror' in error_msg or
                        'connection' in error_msg or
                        'timeout' in error_msg):
                        
                        retries += 1
                        if retries < max_retries:
                            wait_time = delay * (backoff ** (retries - 1))
                            logger.warning(f"Connection error occurred (attempt {retries}/{max_retries})")
                            time.sleep(wait_time)
                        else:
                            logger.error(f"Max retries ({max_retries}) reached. Error: {e}")
                            raise e
                    elif 'already exists' in error_msg:
                        logger.info(f"Resource already exists: {e}")
                        return {'status': 'exists', 'message': str(e)}
                    else:
                        raise e
            return None
        return wrapper
    return decorator

class MindsDBHandler:
    def __init__(self):
        self.server = None
        self.connected = False
        self.last_queries = []  # Track executed queries for transparency
        
        # Load configuration from environment variables
        self.mindsdb_host = os.getenv('MINDSDB_HOST', '127.0.0.1')
        self.mindsdb_port = os.getenv('MINDSDB_PORT', '47334')
        self.ollama_base_url = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
        self.google_api_key = os.getenv('GOOGLE_API_KEY', '')
        self.database_name = os.getenv('MINDSDB_DATABASE', 'legalease')
        
    def _log_query(self, query, operation="query"):
        """Log executed query for transparency"""
        self.last_queries.append({
            'operation': operation,
            'query': query,
            'timestamp': time.time()
        })
        # Keep only last 10 queries
        if len(self.last_queries) > 10:
            self.last_queries = self.last_queries[-10:]
        
    def connect(self):
        """Connect to MindsDB server"""
        try:
            connection_url = f'http://{self.mindsdb_host}:{self.mindsdb_port}'
            self.server = mindsdb_sdk.connect(connection_url)
            self.connected = True
            logger.info(f"Connected to MindsDB at {connection_url}")
            return True
        except Exception as e:
            logger.error(f"MindsDB connection failed: {e}")
            self.connected = False
            return False
    
    def check_ollama_connection(self):
        """Check if Ollama is running and accessible"""
        try:
            ollama_tags_url = f"{self.ollama_base_url}/api/tags"
            response = requests.get(ollama_tags_url, timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def check_status(self):
        """Check system status"""
        mindsdb_status = self.connect() if not self.connected else True
        ollama_status = self.check_ollama_connection()
        
        return {
            'mindsdb': mindsdb_status,
            'ollama': ollama_status,
            'overall': mindsdb_status and ollama_status
        }
    
    @retry_on_error(max_retries=3, delay=3, backoff=2)
    def initialize_system(self):
        """Initialize knowledge base and agent"""
        if not self.connected:
            if not self.connect():
                raise Exception("Failed to connect to MindsDB")
        
        results = []
          # Create knowledge base
        try:
            kb_query = f"""CREATE KNOWLEDGE_BASE {self.database_name}.legal_kb_pg
USING
    embedding_model = {{
        "provider": "ollama",
        "model_name": "mxbai-embed-large",
        "base_url": "{self.ollama_base_url}"
    }},
    reranking_model = {{
        "provider": "gemini",
        "model_name": "gemini-2.0-flash"
    }},
    storage = my_pgvector.legal_kb_pg_storage,
    metadata_columns = ['title', 'category'],
    content_columns = ['content'],
    id_column = 'doc_id';"""
            
            result = self.server.query(kb_query)
            self._log_query(kb_query, operation="create_knowledge_base")
            results.append({'step': 'knowledge_base', 'status': 'success'})
        except Exception as e:
            if 'already exists' in str(e).lower():
                results.append({'step': 'knowledge_base', 'status': 'exists'})
            else:
                raise e
          # Create agent
        try:
            agent_query = f"""CREATE AGENT legal_gemini_agent
USING
    model = 'gemini-2.0-flash',
    google_api_key = '{self.google_api_key}',
    include_knowledge_bases = ['{self.database_name}.legal_kb_pg'],
    prompt_template = '
        You are LegalEase AI, a legal assistant. Use the legal knowledge base to answer questions.
        Quote exact case excerpts if they are relevant.
        Question: {{{{question}}}}
    ';"""
            
            result = self.server.query(agent_query)
            self._log_query(agent_query, operation="create_agent")
            results.append({'step': 'agent', 'status': 'success'})
        except Exception as e:
            if 'already exists' in str(e).lower():
                results.append({'step': 'agent', 'status': 'exists'})
            else:
                raise e
          # Create index
        try:
            index_query = f"CREATE INDEX ON KNOWLEDGE_BASE {self.database_name}.legal_kb_pg;"
            result = self.server.query(index_query)
            self._log_query(index_query, operation="create_index")
            results.append({'step': 'index', 'status': 'success'})
        except Exception as e:
            if 'already exists' in str(e).lower():
                results.append({'step': 'index', 'status': 'exists'})
            else:                results.append({'step': 'index', 'status': 'failed', 'error': str(e)})
        
        return {'success': True, 'results': results}
    
    @retry_on_error(max_retries=3, delay=2, backoff=2)
    def insert_documents(self, df):
        """Insert documents from DataFrame into knowledge base"""
        if not self.connected:
            if not self.connect():
                raise Exception("Failed to connect to MindsDB")
        
        inserted_count = 0
        
        for _, row in df.iterrows():
            try:
                insert_query = f"""INSERT INTO legalease.legal_kb_pg (doc_id, title, category, content) VALUES
({row['doc_id']}, '{row['title'].replace("'", "''")}', '{row['category'].replace("'", "''")}', '{row['content'].replace("'", "''")}');"""
                
                # Log the query for transparency
                self._log_query(insert_query, "insert_document")
                
                result = self.server.query(insert_query)
                inserted_count += 1
                time.sleep(0.5)  # Small delay between inserts
                
            except Exception as e:
                logger.warning(f"Failed to insert document {row.get('doc_id', 'unknown')}: {e}")
        
        return inserted_count
    
    @retry_on_error(max_retries=3, delay=2, backoff=2)
    def semantic_search(self, query, category=None, limit=5):
        """Perform semantic search on knowledge base"""
        if not self.connected:
            if not self.connect():
                raise Exception("Failed to connect to MindsDB")
        
        # Build search query
        search_query = f"""SELECT
  id,
  metadata,
  chunk_content,
  relevance
FROM legalease.legal_kb_pg
WHERE content LIKE '{query}'"""
        
        if category:
            search_query += f" AND JSON_EXTRACT(metadata, '$.category') = '{category}'"
        
        search_query += f" ORDER BY relevance DESC LIMIT {limit};"
        
        # Log the query for transparency
        self._log_query(search_query, "semantic_search")
        
        result = self.server.query(search_query)
        time.sleep(1)  # Allow processing
        df = result.fetch()
        
        # Convert to list of dictionaries
        results = []
        for _, row in df.iterrows():
            results.append({
                'id': row.get('id', ''),
                'content': row.get('chunk_content', ''),
                'relevance': float(row.get('relevance', 0)),
                'metadata': row.get('metadata', '{}')
            })
        
        return results
    
    @retry_on_error(max_retries=3, delay=3, backoff=2)
    def ask_agent(self, question):
        """Ask the AI agent a question"""
        if not self.connected:
            if not self.connect():
                raise Exception("Failed to connect to MindsDB")
        
        agent_query = f"""SELECT answer
FROM legalease.legal_gemini_agent
WHERE question = '{question.replace("'", "''")}';"""
        
        # Log the query for transparency
        self._log_query(agent_query, "ask_agent")
        
        result = self.server.query(agent_query)
        time.sleep(2)  # Allow processing
        df = result.fetch()
        
        if not df.empty:
            return df.iloc[0]['answer']
        else:
            return "No answer received from the agent."
    
    @retry_on_error(max_retries=2, delay=1, backoff=1)
    def get_categories(self):
        """Get available categories from knowledge base"""
        if not self.connected:
            if not self.connect():
                raise Exception("Failed to connect to MindsDB")
        
        try:
            category_query = """SELECT DISTINCT JSON_EXTRACT(metadata, '$.category') as category
FROM legalease.legal_kb_pg
WHERE JSON_EXTRACT(metadata, '$.category') IS NOT NULL
ORDER BY category;"""
            
            result = self.server.query(category_query)
            df = result.fetch()
            categories = [row['category'] for _, row in df.iterrows() if row['category']]
            return categories
        except Exception as e:
            logger.warning(f"Could not fetch categories: {e}")
            return ['Criminal Law', 'Civil Rights', 'Constitutional Law', 'Contract Law', 'Corporate Law']
    
    def get_last_queries(self, limit=5):
        """Get the last executed queries for transparency"""
        return self.last_queries[-limit:] if self.last_queries else []
    
    @retry_on_error(max_retries=3, delay=2, backoff=2)
    def create_job(self, job_name, job_type, schedule, custom_query=None):
        """Create a new MindsDB job"""
        if not self.connected:
            if not self.connect():
                raise Exception("Failed to connect to MindsDB")
        
        logger.info(f"Starting job creation - Name: {job_name}, Type: {job_type}, Schedule: {schedule}")
        
        # Switch to legalease project first
        try:
            switch_query = "USE legalease;"
            self.server.query(switch_query)
            logger.info("Switched to legalease project for job creation")
            
            # Verify current project
            verify_query = "SELECT DATABASE();"
            verify_result = self.server.query(verify_query)
            current_db = verify_result.fetch()
            logger.info(f"Current database after switch: {current_db}")
            
        except Exception as e:
            logger.error(f"Could not switch to legalease project: {e}")
          # Build job query based on type - CREATE JOB within legalease project
        if job_type == 'csv_ingest':
            job_query = f"""CREATE JOB legalease.{job_name}
AS (
  INSERT INTO legalease.legal_kb_pg
  SELECT
    doc_id,
    title,
    category,
    content
  FROM files.legal_docs
  WHERE doc_id > LAST;
)
{schedule};"""
        elif job_type == 'kb_maintenance':
            job_query = f"""CREATE JOB legalease.{job_name}
AS (
  CREATE INDEX ON KNOWLEDGE_BASE legalease.legal_kb_pg;
)
{schedule};"""
        elif job_type == 'index_rebuild':
            job_query = f"""CREATE JOB legalease.{job_name}
AS (
  DROP INDEX ON KNOWLEDGE_BASE legalease.legal_kb_pg;
  CREATE INDEX ON KNOWLEDGE_BASE legalease.legal_kb_pg;
)
{schedule};"""
        elif job_type == 'custom' and custom_query:
            job_query = f"""CREATE JOB legalease.{job_name}
AS (
  {custom_query}
)
{schedule};"""
        else:
            raise Exception("Invalid job type or missing custom query")
        
        # Log the exact query that will be executed
        logger.info(f"About to execute job creation query:")
        logger.info(f"Query: {job_query}")
        
        # Log and execute the query
        self._log_query(job_query, "create_job")
        
        try:
            result = self.server.query(job_query)
            logger.info(f"Job creation query executed, result type: {type(result)}")
            
            # Try to get more details about the result
            try:
                result_df = result.fetch()
                logger.info(f"Job creation result DataFrame: {result_df}")
            except Exception as fetch_e:
                logger.info(f"Could not fetch result DataFrame: {fetch_e}")
            
            time.sleep(2)  # Allow more processing time
              # Immediately verify the job was created by checking SHOW JOBS from legalease
            try:
                verify_jobs_query = "SHOW JOBS FROM legalease;"
                verify_result = self.server.query(verify_jobs_query)
                verify_df = verify_result.fetch()
                logger.info(f"Verification: SHOW JOBS FROM legalease returned {len(verify_df)} jobs after creation")
                if len(verify_df) > 0:
                    job_names = verify_df['NAME'].tolist() if 'NAME' in verify_df.columns else []
                    logger.info(f"Jobs found in legalease: {job_names}")
                    if job_name in job_names:
                        logger.info(f"SUCCESS: Job '{job_name}' found in legalease project!")
                    else:
                        logger.warning(f"WARNING: Job '{job_name}' NOT found in legalease project!")
                        logger.info(f"Expected job name: {job_name}")
                        logger.info(f"Available jobs: {job_names}")
                else:
                    logger.warning("WARNING: No jobs found in legalease project after creation!")
            except Exception as verify_e:
                logger.error(f"Could not verify job creation in legalease: {verify_e}")
            
            logger.info(f"Job creation completed for: {job_name}")
            return {
                'success': True,
                'message': f'Job "{job_name}" created successfully',
                'query': job_query
            }
            
        except Exception as e:
            logger.error(f"Job creation failed with error: {e}")
            logger.error(f"Error type: {type(e)}")
            
            if 'already exists' in str(e).lower():
                return {
                    'success': False,
                    'error': f'Job "{job_name}" already exists'
                }
            else:
                raise e
    
    @retry_on_error(max_retries=2, delay=1, backoff=1)
    def list_jobs(self):
        """List all active MindsDB jobs"""
        if not self.connected:
            if not self.connect():
                raise Exception("Failed to connect to MindsDB")
        
        try:
            # First, switch to legalease project
            switch_query = "USE legalease;"
            self.server.query(switch_query)
            logger.info("Switched to legalease project")
            
            # Check current project
            project_query = "SELECT DATABASE();"
            result = self.server.query(project_query)
            current_project = result.fetch()
            logger.info(f"Current project after switch: {current_project}")
              # Try different variations of SHOW JOBS with more comprehensive queries, prioritizing legalease project
            queries_to_try = [
                "SHOW JOBS FROM legalease;",  # Try legalease project first
                "SHOW JOBS;",
                "SHOW JOBS FROM mindsdb;",
                "SELECT * FROM legalease.information_schema.jobs;",
                "SELECT * FROM information_schema.jobs;",
                "SELECT * FROM mindsdb.information_schema.jobs;",
                "SELECT * FROM mindsdb.jobs;",
                "SHOW FULL JOBS;"
            ]
            
            jobs = []
            for query in queries_to_try:
                try:
                    logger.info(f"Trying query: {query}")
                    self._log_query(query, "list_jobs")
                    
                    result = self.server.query(query)
                    time.sleep(1)  # Allow processing
                    df = result.fetch()
                    
                    logger.info(f"Query '{query}' returned {len(df)} rows")
                    if len(df) > 0:
                        logger.info(f"DataFrame columns: {df.columns.tolist()}")
                        logger.info(f"Sample data: {df.head().to_dict()}")
                    
                    if len(df) > 0:
                        # Found jobs, process them
                        for _, row in df.iterrows():
                            logger.info(f"Processing job row: {row.to_dict()}")
                            
                            # Map MindsDB column names to our format using the actual column names
                            job_name = (row.get('NAME') or row.get('name') or 
                                       row.get('job_name') or row.get('JOB_NAME') or str(row.iloc[0] if len(row) > 0 else ''))
                            
                            job_project = (row.get('PROJECT') or row.get('project') or '')
                            job_schedule = (row.get('SCHEDULE_STR') or row.get('schedule_str') or 
                                          row.get('SCHEDULE') or row.get('schedule') or '')
                            
                            job_query = (row.get('QUERY') or row.get('query') or '')
                            job_status = (row.get('STATUS') or row.get('status') or 'active')
                            
                            # Only include jobs if they have a name
                            if job_name and job_name.strip():
                                jobs.append({
                                    'id': job_name,
                                    'name': job_name,
                                    'project': job_project,
                                    'type': str(job_query)[:50] + '...' if len(str(job_query)) > 50 else str(job_query),
                                    'status': str(job_status) if job_status else 'active',
                                    'schedule': str(job_schedule),
                                    'created_at': str(row.get('START_AT') or row.get('start_at') or ''),
                                    'last_run': str(row.get('NEXT_RUN_AT') or row.get('next_run_at') or '')
                                })
                        
                        logger.info(f"Successfully found {len(jobs)} jobs using query: {query}")
                        if jobs:  # Only break if we actually found jobs
                            break
                        
                except Exception as query_e:
                    logger.warning(f"Query '{query}' failed: {query_e}")
                    continue
            
            logger.info(f"Returning {len(jobs)} jobs")
            return jobs
            
        except Exception as e:
            logger.error(f"Could not fetch jobs: {e}")
            logger.error(f"Exception type: {type(e)}")
            # Return empty list instead of mock data to see the real issue
            return []
    
    @retry_on_error(max_retries=2, delay=1, backoff=1)
    def stop_job(self, job_name):
        """Stop/delete a MindsDB job"""
        if not self.connected:
            if not self.connect():
                raise Exception("Failed to connect to MindsDB")
        
        try:
            # If job_name doesn't include project, add legalease prefix
            if not job_name.startswith('legalease.'):
                full_job_name = f"legalease.{job_name}"
            else:
                full_job_name = job_name
                
            stop_query = f"DROP JOB {full_job_name};"
            logger.info(f"Attempting to stop job with query: {stop_query}")
            
            self._log_query(stop_query, "stop_job")
            
            result = self.server.query(stop_query)
            time.sleep(1)  # Allow processing
            
            return {
                'success': True,
                'message': f'Job "{job_name}" stopped successfully'
            }
        except Exception as e:
            logger.error(f"Failed to stop job '{job_name}': {e}")
            if 'does not exist' in str(e).lower():
                return {
                    'success': False,
                    'error': f'Job "{job_name}" does not exist'
                }
            else:
                raise e
