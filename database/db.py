## for SQLite database connection and operations
import sqlite3
import pandas as pd
import datetime

DB_NAME = 'tasks.db' # Creating a SQLite database named 'tasks.db'

def create_connection():
    """Create a database connection to the SQLite database 
    specified by DB_NAME."""
    conn = sqlite3.connect(DB_NAME, check_same_thread=False) 
    #check_same_thread=False allows streamlit to access the DB from different user sessions without crashing.
    return conn

def init_db():
    """Initialize the database using the tasks table."""
    conn = create_connection()
    cursor = conn.cursor()
    query ="""
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        task_category TEXT NOT NULL,
        task_priority TEXT NOT NULL DEFAULT 'Medium', -- New priority column with default value
        due_date DATE NOT NULL,
        description TEXT NOT NULL,
        status TEXT NOT NULL,
        ai_response TEXT DEFAULT 'pending',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """
    cursor.execute(query) ## Execute the query to create the tasks table
    conn.commit()
    conn.close()
    print("Database initialized sucessfully.")

##For creating tasks##
def add_task(name, task_category, task_priority, due_date, description, status): #saves a new task to the database
    conn = create_connection()
    c = conn.cursor()
    
    # Parameterized Query (Protects against SQL Injection)
    query = """
    INSERT INTO tasks (name, task_category, task_priority, due_date, description, status)
    VALUES (?, ?, ?, ?, ?, ?)
    """
  
    c.execute(query, (name, task_category, task_priority, due_date, description, status))
    conn.commit()
    conn.close()

##For retrieving tasks##
def get_tasks():
    """
    Fetches all tasks and returns them as a Pandas DataFrame.
    This makes it easy to display in Streamlit.
    """
    conn = create_connection()
    
    df = pd.read_sql_query( ## New! (Will sort tasks by due date in ascending order)
    "SELECT * FROM tasks ORDER BY due_date ASC", 
    conn
)
    
    # Convert string dates to actual Date Objects for sorting
    if not df.empty:
        df['due_date'] = pd.to_datetime(df['due_date']).dt.date
        
    return df

##For updating task status##
def update_task_status(task_id, new_status):
    """
    Updates the status of a task (e.g., from 'Pending' to 'Complete').
    """
    conn = create_connection()
    c = conn.cursor()
    
    query = "UPDATE tasks SET status = ? WHERE id = ?"
    c.execute(query, (new_status, task_id))
    
    conn.commit()
    conn.close()

##For deleting tasks##
def delete_task(task_id):
    """Deletes a specific task by its ID."""
    conn = create_connection()
    c = conn.cursor()
    query = "DELETE FROM tasks WHERE id = ?"
    c.execute(query, (task_id,))
    conn.commit()
    conn.close()

##For editing tasks##
def edit_task(task_id, new_name, new_category, new_priority, new_due_date, new_description):
    """Updates the details of an existing task."""
    conn = create_connection()
    c = conn.cursor()
    query = """
    UPDATE tasks 
    SET name = ?, task_category = ?, task_priority = ?, due_date = ?, description = ?
    WHERE id = ?
    """
    c.execute(query, (new_name, new_category, new_priority, new_due_date, new_description, task_id))
    conn.commit()
    conn.close()

##For AI response##
def save_ai_response(task_id, ai_response):
    """Saves the AI response for a specific task."""
    conn = create_connection()
    c = conn.cursor()
    query = "UPDATE tasks SET ai_response = ? WHERE id = ?"
    c.execute(query, (ai_response, task_id))
    conn.commit()
    conn.close()