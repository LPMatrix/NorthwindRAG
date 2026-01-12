import os
import mysql.connector
import json
import ollama
import chromadb
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', ''),
    'database': os.getenv('DB_NAME', 'northwind')
}

def get_db_connection():
    return mysql.connector.connect(**DB_CONFIG)

def extract_tables():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SHOW TABLES")
    tables = [table[0] for table in cursor.fetchall()]
    
    cursor.close()
    conn.close()
    return tables

def extract_table_schema(table_name):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute(f"DESCRIBE {table_name}")
    columns = cursor.fetchall()
    
    cursor.execute(f"""
        SELECT 
            COLUMN_NAME,
            REFERENCED_TABLE_NAME,
            REFERENCED_COLUMN_NAME
        FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
        WHERE TABLE_SCHEMA = 'northwind'
        AND TABLE_NAME = '{table_name}'
        AND REFERENCED_TABLE_NAME IS NOT NULL
    """)
    foreign_keys = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return {
        'table': table_name,
        'columns': columns,
        'foreign_keys': foreign_keys
    }

def schema_to_text(schema):
    table = schema['table']
    columns = schema['columns']
    fks = schema['foreign_keys']
    
    text = f"Table: {table}\n"
    text += "Columns:\n"
    
    for col in columns:
        text += f"  - {col['Field']} ({col['Type']})"
        if col['Key'] == 'PRI':
            text += " [PRIMARY KEY]"
        if col['Null'] == 'NO':
            text += " [NOT NULL]"
        text += "\n"
    
    if fks:
        text += "Foreign Keys:\n"
        for fk in fks:
            text += f"  - {fk['COLUMN_NAME']} references {fk['REFERENCED_TABLE_NAME']}.{fk['REFERENCED_COLUMN_NAME']}\n"
    
    return text

def generate_embedding(text):
    response = ollama.embeddings(model='nomic-embed-text', prompt=text)
    return response['embedding']

def main():
    print("Extracting schema from Northwind database...")
    
    tables = extract_tables()
    print(f"Found {len(tables)} tables: {', '.join(tables)}")
    
    schemas = []
    for table in tables:
        print(f"Processing {table}...")
        schema = extract_table_schema(table)
        text = schema_to_text(schema)
        schemas.append({
            'table': table,
            'schema': schema,
            'text': text
        })
    
    print("\nGenerating embeddings and storing in ChromaDB...")
    client = chromadb.PersistentClient(path="./chroma_db_northwind")
    
    try:
        client.delete_collection("northwind_schema")
    except:
        pass
    
    collection = client.create_collection("northwind_schema")
    
    for item in schemas:
        print(f"Embedding {item['table']}...")
        embedding = generate_embedding(item['text'])
        
        collection.add(
            embeddings=[embedding],
            documents=[item['text']],
            metadatas=[{
                'table': item['table'],
                'schema': json.dumps(item['schema'])
            }],
            ids=[item['table']]
        )
    
    print("\nSchema extraction complete!")
    print(f"Stored {len(schemas)} table schemas in vector database")
    
    print("\nSample schema text:")
    print("=" * 60)
    print(schemas[0]['text'])

if __name__ == "__main__":
    main()