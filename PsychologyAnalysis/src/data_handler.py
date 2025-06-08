# 文件路径: src/data_handler.py
import sqlite3
import json
import os
from datetime import datetime

class DataHandler:
    def __init__(self, db_path="psychology_analysis.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initializes the database schema more robustly."""
        print(f"Initializing database schema at: {self.db_path}")
        required_columns_analysis = {
            # 列名: 列类型 (不包含约束和复杂默认值，这些在CREATE TABLE中处理)
            "image_path": "TEXT",
            "subject_name": "TEXT",
            "age": "INTEGER",
            "gender": "TEXT",
            "questionnaire_type": "TEXT",
            "questionnaire_data": "TEXT", # JSON
            "report_text": "TEXT",
            "updated_at": "TIMESTAMP", # 类型即可，默认值由触发器处理
            "id_card": "TEXT", # 类型即可，UNIQUE在CREATE TABLE中处理
            "occupation": "TEXT",
            "case_name": "TEXT",
            "case_type": "TEXT",
            "identity_type": "TEXT",
            "person_type": "TEXT",
            "marital_status": "TEXT",
            "children_info": "TEXT",
            "criminal_record": "INTEGER",
            "health_status": "TEXT",
            "phone_number": "TEXT",
            "domicile": "TEXT"
        }
        # questionnaire_questions 列
        required_columns_questions = {
            "scale_name": "TEXT"
        }


        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # --- Handle analysis_data Table ---
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='analysis_data';")
            table_exists = cursor.fetchone()

            if not table_exists:
                print("Table 'analysis_data' does not exist. Creating new table with full schema...")
                # Create table with all columns and constraints if it doesn't exist
                create_table_sql = """
                CREATE TABLE analysis_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    image_path TEXT,
                    subject_name TEXT,
                    age INTEGER,
                    gender TEXT,
                    questionnaire_type TEXT,
                    questionnaire_data TEXT,
                    report_text TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- Initial value
                    id_card TEXT , 
                    occupation TEXT,
                    case_name TEXT,
                    case_type TEXT,
                    identity_type TEXT,
                    person_type TEXT,
                    marital_status TEXT,
                    children_info TEXT,
                    criminal_record INTEGER DEFAULT 0,
                    health_status TEXT,
                    phone_number TEXT,
                    domicile TEXT
                );
                """
                cursor.execute(create_table_sql)
                print("Table 'analysis_data' created successfully.")
            else:
                print("Table 'analysis_data' exists. Checking for missing columns...")
                # If table exists, check and add missing columns without problematic constraints/defaults
                cursor.execute("PRAGMA table_info(analysis_data)")
                existing_columns = {info[1] for info in cursor.fetchall()}

                for col_name, col_type in required_columns_analysis.items():
                    if col_name not in existing_columns:
                        try:
                            # Add column with only the type, no complex defaults or UNIQUE constraints here
                            cursor.execute(f"ALTER TABLE analysis_data ADD COLUMN {col_name} {col_type}")
                            print(f"Added column '{col_name}' to analysis_data table.")
                        except sqlite3.OperationalError as e:
                            print(f"Warning: Could not add column '{col_name}': {e}")

            # --- Handle questionnaire_questions Table ---
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='questionnaire_questions';")
            q_table_exists = cursor.fetchone()
            if not q_table_exists:
                 print("Table 'questionnaire_questions' does not exist. Creating new table...")
                 cursor.execute('''CREATE TABLE questionnaire_questions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    questionnaire_type TEXT NOT NULL,
                    question_number INTEGER NOT NULL,
                    question_text TEXT NOT NULL,
                    options TEXT NOT NULL, -- JSON string
                    scale_name TEXT, -- User-friendly name
                    UNIQUE(questionnaire_type, question_number)
                )''')
                 print("Table 'questionnaire_questions' created successfully.")
            else:
                 print("Table 'questionnaire_questions' exists. Checking for missing columns...")
                 cursor.execute("PRAGMA table_info(questionnaire_questions)")
                 existing_q_columns = {info[1] for info in cursor.fetchall()}
                 for col_name, col_type in required_columns_questions.items():
                      if col_name not in existing_q_columns:
                           try:
                                cursor.execute(f"ALTER TABLE questionnaire_questions ADD COLUMN {col_name} {col_type}")
                                print(f"Added column '{col_name}' to questionnaire_questions table.")
                           except sqlite3.OperationalError as e:
                                print(f"Warning: Could not add column '{col_name}' to questionnaire_questions: {e}")


            # --- Ensure Triggers Exist ---
            # Trigger to update 'updated_at' timestamp (safe to run even if exists)
            try:
                 cursor.execute('''
                    CREATE TRIGGER IF NOT EXISTS update_analysis_data_updated_at
                    AFTER UPDATE ON analysis_data
                    FOR EACH ROW
                    WHEN OLD.updated_at = NEW.updated_at OR OLD.updated_at IS NULL -- Avoid infinite loops if trigger itself updates
                    BEGIN
                        UPDATE analysis_data SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
                    END;
                ''')
                 print("Ensured 'updated_at' trigger exists.")
            except sqlite3.OperationalError as e:
                 print(f"Warning: Could not create/verify 'updated_at' trigger: {e}")


            conn.commit()
        print("Database schema initialization process completed.")
    def normalize_path(self, path):
        """Normalizes file path for consistency, returns None if path is None."""
        if path is None:
            return None
        return os.path.normpath(path).replace('\\', '/')

    def save_data(self, image_path, basic_info, scale_type, scale_answers_json):
        """Saves comprehensive data to the analysis_data table."""
        normalized_image_path = self.normalize_path(image_path) # Can be None

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # Prepare column names and placeholders dynamically based on basic_info keys
            # Always include mandatory fields
            columns = ['image_path', 'questionnaire_type', 'questionnaire_data']
            placeholders = ['?', '?', '?']
            values = [normalized_image_path, scale_type, scale_answers_json]

            # Add fields from basic_info
            for key, value in basic_info.items():
                # Map form names to DB column names if necessary
                db_key = key # Assume direct mapping for now
                # Handle specific fields like subject_name, age, gender if they are part of basic_info
                if db_key == "name": db_key = "subject_name"

                # Ensure the key is a valid column name (check against required_columns keys)
                # This is a basic check; more robust validation might be needed
                valid_columns = { "subject_name", "age", "gender", "id_card", "occupation", "case_name", "case_type", "identity_type", "person_type", "marital_status", "children_info", "criminal_record", "health_status", "phone_number", "domicile"}
                if db_key in valid_columns:
                    columns.append(db_key)
                    placeholders.append('?')
                    # Special handling for criminal_record (assuming 1 for Yes, 0 for No from form)
                    if db_key == 'criminal_record':
                        values.append(1 if str(value).lower() in ['1', 'yes', 'true'] else 0)
                    else:
                        values.append(value)

            columns_str = ", ".join(columns)
            placeholders_str = ", ".join(placeholders)

            sql = f'''INSERT INTO analysis_data ({columns_str})
                      VALUES ({placeholders_str})'''

            try:
                cursor.execute(sql, values)
                submission_id = cursor.lastrowid
                conn.commit()
                print(f"Data saved successfully. Submission ID: {submission_id}")
                return submission_id
            except sqlite3.IntegrityError as e:
                 print(f"Error saving data: {e}. Possible duplicate entry (e.g., ID card)?")
                 # Depending on requirements, you might want to update instead of insert
                 # Or simply report the error
                 raise e # Re-raise the exception
            except Exception as e:
                 print(f"An unexpected error occurred during save: {e}")
                 raise e


    def load_data_by_id(self, submission_id):
        """Loads a submission's data by its ID, returning a dictionary."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row # Return rows as dictionary-like objects
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM analysis_data WHERE id = ?", (submission_id,))
            result = cursor.fetchone()
            if result:
                return dict(result) # Convert Row object to a standard dictionary
            return None

    def update_report_text(self, submission_id, report_text):
        """Updates the report_text for a given submission ID."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE analysis_data SET report_text = ? WHERE id = ?",
                           (report_text, submission_id))
            conn.commit()
            print(f"Report text updated for submission ID: {submission_id}")

    def load_questions_by_type(self, questionnaire_type_code):
        """Loads questions based on the questionnaire type code (e.g., 'SAS')."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''SELECT question_number, question_text, options
                            FROM questionnaire_questions
                            WHERE questionnaire_type = ?
                            ORDER BY question_number''', (questionnaire_type_code,))
            results = cursor.fetchall()
            questions = []
            if not results:
                 print(f"Warning: No questions found for type code '{questionnaire_type_code}'")
                 return None # Return None or empty list based on how you want to handle this
            for row in results:
                try:
                    options_list = json.loads(row[2])
                    # Ensure options have 'text' (or 'name') and 'score' keys
                    formatted_options = [
                        {"text": opt.get("text", opt.get("name", "N/A")), "score": opt.get("score", 0)}
                        for opt in options_list
                    ]
                    question = {
                        "number": row[0],
                        "text": row[1],
                        "options": formatted_options
                    }
                    questions.append(question)
                except json.JSONDecodeError:
                    print(f"Warning: Could not decode options for question {row[0]} of type {questionnaire_type_code}")
                except Exception as e:
                     print(f"Error processing question {row[0]} options: {e}")
            return questions


    def insert_question(self, questionnaire_type, question_number, question_text, options_json_str, scale_name=None):
        """Inserts a single question into the database."""
        # The options should already be a JSON string here if coming from import_questions
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            try:
                cursor.execute('''INSERT OR REPLACE INTO questionnaire_questions
                                (questionnaire_type, question_number, question_text, options, scale_name)
                                VALUES (?, ?, ?, ?, ?)''', (
                    questionnaire_type,
                    question_number,
                    question_text,
                    options_json_str, # Store as JSON string
                    scale_name if scale_name else questionnaire_type # Default scale_name to type if not provided
                ))
                conn.commit()
                # print(f"Inserted/Replaced question: {questionnaire_type} - Q{question_number}")
            except Exception as e:
                 print(f"Error inserting question {questionnaire_type}-Q{question_number}: {e}")

    def get_all_scale_types(self):
        """Retrieves distinct scale types (code and name) from the database."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # Use COALESCE to provide the type code if name is NULL
            cursor.execute('''SELECT DISTINCT questionnaire_type, COALESCE(scale_name, questionnaire_type) as display_name
                            FROM questionnaire_questions
                            ORDER BY questionnaire_type''')
            results = cursor.fetchall()
            # Return as a list of dictionaries
            return [{"code": row[0], "name": row[1]} for row in results]


def check_db_content(db_path="psychology_analysis.db"):
    """Utility function to print the content of the analysis_data table."""
    print(f"\n--- Checking content of {db_path} ---")
    if not os.path.exists(db_path):
        print("Database file does not exist.")
        return

    try:
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            print("\n[analysis_data Table Content]")
            try:
                cursor.execute("SELECT * FROM analysis_data LIMIT 10") # Limit output for brevity
                rows = cursor.fetchall()
                if not rows:
                    print("Table is empty.")
                else:
                    # Print header
                    print(" | ".join(rows[0].keys()))
                    print("-" * (len(" | ".join(rows[0].keys())) + 10))
                    # Print rows
                    for row in rows:
                        print(" | ".join(map(str, row)))
            except sqlite3.OperationalError as e:
                print(f"Error querying analysis_data: {e}")


            print("\n[questionnaire_questions Table Content]")
            try:
                cursor.execute("SELECT DISTINCT questionnaire_type, scale_name FROM questionnaire_questions")
                scales = cursor.fetchall()
                if not scales:
                    print("Table is empty or contains no distinct scales.")
                else:
                    print("Available Scales (Type | Name):")
                    for scale in scales:
                        print(f"{scale['questionnaire_type']} | {scale['scale_name']}")

                # Optionally print a few questions per scale
                if scales:
                     print("\nSample Questions:")
                     for scale in scales[:2]: # Limit to first 2 scales for brevity
                         print(f"--- Scale: {scale['questionnaire_type']} ---")
                         cursor.execute("SELECT question_number, question_text FROM questionnaire_questions WHERE questionnaire_type = ? ORDER BY question_number LIMIT 3", (scale['questionnaire_type'],))
                         questions = cursor.fetchall()
                         for q in questions:
                             print(f"  Q{q['question_number']}: {q['question_text'][:50]}...") # Truncate long text

            except sqlite3.OperationalError as e:
                print(f"Error querying questionnaire_questions: {e}")

    except sqlite3.Error as e:
        print(f"An error occurred connecting to or reading the database: {e}")
    print("--- End of content check ---\n")


# Example usage (can be run directly to check DB)
if __name__ == "__main__":
     # Assume db is in the project root relative to this file's location (src/)
     project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
     db_file_path = os.path.join(project_root, "psychology_analysis.db")
     # Initialize schema first (important if DB or tables don't exist)
     print("Initializing DataHandler to ensure schema exists...")
     try:
         handler = DataHandler(db_path=db_file_path)
         print("DataHandler initialized.")
         # Now check content
         check_db_content(db_file_path)
         print("\nAvailable scale types:")
         print(handler.get_all_scale_types())
     except Exception as e:
          print(f"Error during DataHandler initialization or check: {e}")