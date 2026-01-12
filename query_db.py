import mysql.connector
import ollama
import chromadb
import json

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'northwind'
}

def get_db_connection():
    return mysql.connector.connect(**DB_CONFIG)

def generate_embedding(text):
    response = ollama.embeddings(model='nomic-embed-text', prompt=text)
    return response['embedding']

def retrieve_relevant_schemas(query, n_results=5):
    client = chromadb.PersistentClient(path="./chroma_db_northwind")
    collection = client.get_collection("northwind_schema")
    
    query_embedding = generate_embedding(query)
    
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results
    )
    
    return results

def generate_sql(query, schema_context):
    prompt = f"""You are a SQL expert. Given a natural language question and database schema context, generate a valid MySQL query.

Database Schema:
{schema_context}

Question: {query}

Important rules:
- Return ONLY the SQL query, no explanation or markdown
- Use proper MySQL syntax
- Use table and column names exactly as shown in the schema
- Include appropriate JOINs when querying related tables
- Limit results to 20 rows unless specifically asked for more

SQL Query:"""
    
    response = ollama.chat(
        model='llama3.2',
        messages=[{'role': 'user', 'content': prompt}]
    )
    
    sql = response['message']['content'].strip()
    sql = sql.replace('```sql', '').replace('```', '').strip()
    
    return sql

def execute_sql(sql):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute(sql)
        results = cursor.fetchall()
        cursor.close()
        conn.close()
        return results, None
    except Exception as e:
        cursor.close()
        conn.close()
        return None, str(e)

def format_results(query, sql, results):
    results_text = json.dumps(results, indent=2, default=str)
    
    prompt = f"""You are a helpful database assistant. A user asked a question, we executed a SQL query, and got results.

User Question: {query}

SQL Query Executed:
{sql}

Query Results:
{results_text}

Provide a natural language answer to the user's question based on these results. Be concise and direct. If there are many results, summarize the key findings."""
    
    response = ollama.chat(
        model='llama3.2',
        messages=[{'role': 'user', 'content': prompt}]
    )
    
    return response['message']['content']

def main():
    print("Northwind Database RAG System (Text-to-SQL)")
    print("=" * 60)
    
    while True:
        query = input("\nAsk a question about the database (or 'quit'): ")
        
        if query.lower() in ['quit', 'exit', 'q']:
            break
        
        print("\n[1/4] Retrieving relevant schema...")
        schema_results = retrieve_relevant_schemas(query)
        
        schemas = schema_results['documents'][0]
        tables = [meta['table'] for meta in schema_results['metadatas'][0]]
        
        print(f"[2/4] Found relevant tables: {', '.join(tables)}")
        
        schema_context = "\n\n".join(schemas)
        
        print("[3/4] Generating SQL query...")
        sql = generate_sql(query, schema_context)
        
        print(f"\nGenerated SQL:\n{sql}\n")
        
        print("[4/4] Executing query...")
        results, error = execute_sql(sql)
        
        if error:
            print(f"\n❌ SQL Error: {error}")
            print("The LLM generated invalid SQL. Try rephrasing your question.")
            continue
        
        if not results:
            print("\n✓ Query executed successfully but returned no results.")
            continue
        
        print(f"\n✓ Found {len(results)} results")
        
        print("\n" + "=" * 60)
        print("Answer:")
        answer = format_results(query, sql, results)
        print(answer)
        print("=" * 60)

if __name__ == "__main__":
    main()