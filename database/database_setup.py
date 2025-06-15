# database/database_setup.py

import sqlite3
import logging
import os
import json

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Define the database path
DB_PATH = os.path.join(os.path.dirname(__file__), 'dsa_problems.db')

def init_db():
    """Initialize SQLite database with problems, test cases, and a session table."""
    # This function remains the same as before
    if os.path.exists(DB_PATH):
        logger.info("Database already exists. Verifying tables.")
    
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Create tables
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS problems (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL UNIQUE,
            description TEXT NOT NULL,
            difficulty TEXT NOT NULL,
            starter_code TEXT,
            hints TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS test_cases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            problem_id INTEGER NOT NULL,
            input TEXT NOT NULL,
            expected_output TEXT NOT NULL,
            FOREIGN KEY (problem_id) REFERENCES problems (id)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS session_summaries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_name TEXT NOT NULL,
            session_id TEXT NOT NULL,
            problem_title TEXT NOT NULL,
            summary TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    problems = [
        {'title': 'Two Sum', 'description': 'Given an array of integers nums and an integer target, return indices of the two numbers such that they add up to target.', 'difficulty': 'Easy'},
        {'title': 'Reverse Linked List', 'description': 'Given the head of a singly linked list, reverse the list, and return the reversed list.', 'difficulty': 'Easy'},
        {'title': 'Valid Parentheses', 'description': 'Given a string s containing just the characters `(`, `)`, `{`, `}`, `[` and `]`, determine if the input string is valid.', 'difficulty': 'Easy'},
        {'title': 'Longest Substring Without Repeating Characters', 'description': 'Given a string `s`, find the length of the longest substring without repeating characters.', 'difficulty': 'Medium'},
        {'title': '3Sum', 'description': 'Given an integer array nums, return all the triplets [nums[i], nums[j], nums[k]] such that i != j, i != k, and j != k, and nums[i] + nums[j] + nums[k] == 0.', 'difficulty': 'Medium'},
        {'title': 'Merge Intervals', 'description': 'Given an array of intervals where intervals[i] = [starti, endi], merge all overlapping intervals, and return an array of the non-overlapping intervals that cover all the intervals in the input.', 'difficulty': 'Medium'},
        {'title': 'Top K Frequent Elements', 'description': 'Given an integer array nums and an integer k, return the k most frequent elements.', 'difficulty': 'Medium'},
        {'title': 'Word Ladder', 'description': 'A transformation sequence from word beginWord to word endWord using a dictionary wordList is a sequence of words beginWord -> s1 -> s2 -> ... -> sk such that every adjacent pair of words differs by a single letter.', 'difficulty': 'Hard'},
        {'title': 'LRU Cache', 'description': 'Design a data structure that follows the constraints of a Least Recently Used (LRU) cache.', 'difficulty': 'Hard'},
        {'title': 'Median of Two Sorted Arrays', 'description': 'Given two sorted arrays nums1 and nums2 of size m and n respectively, return the median of the two sorted arrays.', 'difficulty': 'Hard'}
    ]
    for p in problems:
      p['starter_code'] = 'def solution():\n  pass'
      p['hints'] = '["Hint 1", "Hint 2"]'

    for problem in problems:
        cursor.execute('''
            INSERT OR IGNORE INTO problems (title, description, difficulty, starter_code, hints)
            VALUES (:title, :description, :difficulty, :starter_code, :hints)
        ''', problem)
    conn.commit()
    conn.close()
    logger.info("Database initialized/verified successfully.")

def save_session_summary(user_name: str, session_id: str, problem_title: str, summary: str):
    """Saves a session summary to the database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO session_summaries (user_name, session_id, problem_title, summary)
        VALUES (?, ?, ?, ?)
    ''', (user_name, session_id, problem_title, summary))
    conn.commit()
    conn.close()
    logger.info(f"Saved session summary for user '{user_name}'.")

def get_user_summaries(user_name: str) -> list[str]:
    """Retrieves the last 5 session summaries for a user."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT summary FROM session_summaries WHERE user_name = ? ORDER BY timestamp DESC LIMIT 5", (user_name,))
    summaries = [row[0] for row in cursor.fetchall()]
    conn.close()
    return summaries

# --- MISSING FUNCTIONS ADDED BELOW ---

def get_all_problem_titles() -> list[dict]:
    """Get all problem titles with their IDs for the UI selector."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT id, title FROM problems ORDER BY id')
    problems = [{'id': row[0], 'title': row[1]} for row in cursor.fetchall()]
    conn.close()
    return problems

def get_problem_details(problem_id: int) -> dict | None:
    """Retrieve all details for a given problem, including test cases."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    problem = cursor.execute('SELECT * FROM problems WHERE id = ?', (problem_id,)).fetchone()
    if not problem:
        conn.close()
        return None
        
    test_cases = cursor.execute('SELECT input, expected_output FROM test_cases WHERE problem_id = ?', (problem_id,)).fetchall()
    conn.close()
    
    problem_dict = dict(problem)
    # Note: test cases will be empty unless you add them to the database
    problem_dict['test_cases'] = [{'input': tc['input'], 'expected_output': tc['expected_output']} for tc in test_cases]
    
    return problem_dict

if __name__ == '__main__':
    init_db()