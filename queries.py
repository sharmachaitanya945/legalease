import mindsdb_sdk
import time
from functools import wraps
import requests

def retry_on_litellm_error(max_retries=3, delay=2, backoff=2):
    """Decorator to retry function calls when litellm errors occur"""
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
                        'connection' in error_msg):
                        
                        retries += 1
                        if retries < max_retries:
                            wait_time = delay * (backoff ** (retries - 1))
                            print(f"⚠️  Connection error occurred (attempt {retries}/{max_retries})")
                            print(f"   Retrying in {wait_time} seconds...")
                            time.sleep(wait_time)
                        else:
                            print(f"❌ Max retries ({max_retries}) reached. Error: {e}")
                            raise e
                    elif 'already exists' in error_msg:
                        # Handle "already exists" errors (like agents, knowledge bases)
                        print(f"⚠️  Resource already exists: {e}")
                        print("   Continuing with existing resource...")
                        return None  # Return None to indicate handled error
                    else:
                        # Re-raise non-connection errors immediately
                        raise e
            return None
        return wrapper
    return decorator

def check_ollama_connection():
    """Check if Ollama is running and accessible"""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            print("✅ Ollama is running and accessible")
            return True
        else:
            print(f"⚠️  Ollama responded with status code: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"⚠️  Ollama connection check failed: {e}")
        print("   Make sure Ollama is running on localhost:11434")
        return False

def connect_to_mindsdb():
    """Connect to MindsDB server"""
    try:
        # Connect to MindsDB
        server = mindsdb_sdk.connect('http://127.0.0.1:47334')
        print("✅ Connected to MindsDB successfully")
        return server
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return None

@retry_on_litellm_error(max_retries=3, delay=3, backoff=2)
def run_query(server, query, description):
    """Execute a query and handle results"""
    print(f"\n🔄 Executing: {description}")
    print(f"Query: {query}")
    
    try:
        result = server.query(query)
        print("✅ Query executed successfully")
        
        # Try to fetch results if it's a SELECT query
        if query.strip().upper().startswith('SELECT'):
            # Add a small delay before fetching to allow embedding processing
            time.sleep(1)
            df = result.fetch()
            print(f"📊 Results ({len(df)} rows):")
            print(df.to_string())
        else:
            print("✅ Command completed successfully")
            
    except Exception as e:
        print(f"❌ Query failed: {e}")
        # Re-raise to allow retry decorator to handle it
        raise e
    
    print("-" * 80)

def main():
    """Main function to execute all legalease queries"""
    print("🚀 Starting LegalEase MindsDB Queries")
    print("=" * 80)
    
    # Check if Ollama is running
    print("\n🔍 Checking Ollama connectivity...")
    ollama_ok = check_ollama_connection()
    if not ollama_ok:
        print("⚠️  Warning: Ollama may not be accessible. Embedding queries might fail.")
        print("   Please ensure Ollama is running with: docker run -d -p 11434:11434 ollama/ollama")
    
    # Connect to MindsDB
    server = connect_to_mindsdb()
    if not server:
        return
    
    # List of queries to execute
    queries = [
        {
            "query": """CREATE KNOWLEDGE_BASE legalease.legal_kb_pg
USING
    embedding_model = {
        "provider": "ollama",
        "model_name": "mxbai-embed-large",
        "base_url": "http://host.docker.internal:11434"
    },
    reranking_model = {
        "provider": "gemini",
        "model_name": "gemini-2.0-flash"
    },
    storage = my_pgvector.legal_kb_pg_storage,
    metadata_columns = ['title', 'category'],
    content_columns = ['content'],
    id_column = 'doc_id';""",
            "description": "Create Knowledge Base with PGVector"
        },
        {
            "query": """INSERT INTO legalease.legal_kb_pg (doc_id, title, category, content) VALUES
(1, 'Miranda v. Arizona', 'Criminal Law', 'In Miranda v. Arizona, the Supreme Court held that detained criminal suspects must be informed of their rights to an attorney and against self-incrimination prior to police questioning.'),
(2, 'Roe v. Wade', 'Reproductive Rights', 'Roe v. Wade was a landmark decision in which the Court ruled that the Constitution protects a woman\'s right to have an abortion.'),
(3, 'Brown v. Board of Education', 'Civil Rights', 'This decision declared state laws establishing separate public schools for black and white students unconstitutional, effectively ending racial segregation in schools.'),
(4, 'Gideon v. Wainwright', 'Right to Counsel', 'The Court held that the Sixth Amendment requires states to provide attorneys for defendants in criminal cases who cannot afford their own.'),
(5, 'Tinker v. Des Moines', 'Free Speech', 'This case established that students do not "shed their constitutional rights to freedom of speech or expression at the schoolhouse gate."'),
(6, 'Obergefell v. Hodges', 'LGBTQ+ Rights', 'The Court held that the fundamental right to marry is guaranteed to same-sex couples under the Due Process and Equal Protection Clauses.'),
(7, 'New York Times v. United States', 'Freedom of the Press', 'The ruling made it possible for the New York Times and Washington Post to publish the Pentagon Papers without risk of government censorship.'),
(8, 'Plessy v. Ferguson', 'Segregation', 'Although later overturned, this case upheld the constitutionality of racial segregation laws for public facilities under the doctrine of "separate but equal."'),
(9, 'Citizens United v. FEC', 'Campaign Finance', 'The Court held that corporate funding of independent political broadcasts in candidate elections cannot be limited under the First Amendment.'),
(10, 'Texas v. Johnson', 'Symbolic Speech', 'In this case, the Supreme Court invalidated prohibitions on desecrating the American flag enforced in 48 of the 50 states.');""",
            "description": "Insert initial legal documents into Knowledge Base"
        },
        {
            "query": """SELECT * FROM files.legal_docs LIMIT 5;""",
            "description": "Check uploaded legal documents file"
        },
        {
            "query": """SELECT
  id,
  metadata,
  chunk_content,
  relevance
FROM legalease.legal_kb_pg
WHERE content LIKE 'What are my rights if I am arrested?'
ORDER BY relevance DESC
LIMIT 3;""",
            "description": "Query semantically using LIKE - Rights when arrested"
        },
        {
            "query": """CREATE INDEX ON KNOWLEDGE_BASE legalease.legal_kb_pg;""",
            "description": "Create Index on Knowledge Base (requires PGVector)"
        },
        {
            "query": """INSERT INTO legal_kb_pg
SELECT
  doc_id,
  title,
  category,
  content
FROM files.legal_docs
WHERE doc_id > LAST;""",
            "description": "Insert documents from CSV file into Knowledge Base"
        },        {
            "query": """CREATE JOB ingest_from_csv
AS (
  INSERT INTO legal_kb_pg
  SELECT
    doc_id,
    title,
    category,
    content
  FROM files.legal_docs
  WHERE doc_id > LAST;
)
EVERY 1 HOUR;""",
            "description": "Create JOB for automatic CSV ingestion every hour"
        },
        {
            "query": """CREATE AGENT legal_gemini_agent
USING
    model = 'gemini-2.0-flash',
    google_api_key = 'AIzaSyBsV2B_m1wzaGgljBBQaDTHidQw_15OIEs',
    include_knowledge_bases = ['legalease.legal_kb_pg'],
    prompt_template = '
        You are LegalEase AI, a legal assistant. Use the legal knowledge base to answer questions.
        Quote exact case excerpts if they''re relevant.
        Question: {{question}}
    ';""",
            "description": "Create LegalEase AI Agent with Gemini (may already exist)"
        },
        {
            "query": """SELECT answer
FROM legalease.legal_gemini_agent
WHERE question = 'What was the outcome of Gideon v. Wainwright?';""",
            "description": "Test the AI agent with a legal question"
        }
    ]
      # Execute each query
    for i, query_info in enumerate(queries, 1):
        print(f"\n📝 Step {i}/{len(queries)}")
        try:
            run_query(server, query_info["query"], query_info["description"])
        except Exception as e:
            print(f"❌ Failed to execute step {i} after all retries: {e}")
            print("⚠️  Continuing with next query...")
        
        # Add a longer delay between queries to prevent connection issues
        time.sleep(2)
    
    print("\n🎉 All queries completed!")
    print("=" * 80)

@retry_on_litellm_error(max_retries=3, delay=3, backoff=2)
def run_semantic_search(server, question):
    """Run a semantic search query"""
    query = f"""SELECT
  id,
  metadata,
  chunk_content,
  relevance
FROM legalease.legal_kb_pg
WHERE content LIKE '{question}'
ORDER BY relevance DESC
LIMIT 5;"""
    
    run_query(server, query, f"Semantic search for: {question}")

def interactive_search():
    """Interactive mode for searching the knowledge base"""
    server = connect_to_mindsdb()
    if not server:
        return
    
    print("\n🔍 Interactive Legal Knowledge Base Search")
    print("Type 'exit' to quit")
    print("-" * 50)
    
    while True:
        question = input("\nEnter your legal question: ").strip()
        if question.lower() in ['exit', 'quit', 'q']:
            break
        
        if question:
            run_semantic_search(server, question)

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "search":
        # Run in interactive search mode
        interactive_search()
    else:
        # Run all setup queries
        main()
