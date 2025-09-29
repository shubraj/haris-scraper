"""
History Manager for Harris County Property Scraper
Tracks run history, process status, and results.
"""
import sqlite3
import json
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import os

class HistoryManager:
    """Manages run history and process tracking."""
    
    def __init__(self, db_path: str = "harris_scraper_history.db"):
        """Initialize history manager with SQLite database."""
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Initialize the SQLite database with required tables."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Create runs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id TEXT UNIQUE NOT NULL,
                    start_time TIMESTAMP NOT NULL,
                    end_time TIMESTAMP,
                    status TEXT NOT NULL,
                    total_records INTEGER,
                    records_processed INTEGER,
                    addresses_found INTEGER,
                    success_rate REAL,
                    instrument_types TEXT,
                    date_range TEXT,
                    error_message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create process_logs table for real-time tracking
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS process_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id TEXT NOT NULL,
                    timestamp TIMESTAMP NOT NULL,
                    stage TEXT NOT NULL,
                    message TEXT,
                    records_processed INTEGER,
                    addresses_found INTEGER,
                    progress_percentage REAL,
                    FOREIGN KEY (run_id) REFERENCES runs (run_id)
                )
            """)
            
            # Create results table for storing actual results
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id TEXT NOT NULL,
                    file_no TEXT,
                    grantor TEXT,
                    grantee TEXT,
                    instrument_type TEXT,
                    recording_date TEXT,
                    film_code TEXT,
                    legal_description TEXT,
                    property_address TEXT,
                    source TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (run_id) REFERENCES runs (run_id)
                )
            """)
            
            conn.commit()
    
    def start_run(self, run_id: str, instrument_types: List[str], date_range: str) -> bool:
        """Start tracking a new run."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO runs (run_id, start_time, status, instrument_types, date_range)
                    VALUES (?, ?, ?, ?, ?)
                """, (run_id, datetime.now(), 'running', json.dumps(instrument_types), date_range))
                conn.commit()
                return True
        except Exception as e:
            print(f"Error starting run: {e}")
            return False
    
    def update_run_progress(self, run_id: str, records_processed: int, addresses_found: int, 
                          stage: str, message: str = "", progress_percentage: float = 0.0) -> bool:
        """Update run progress and log process step."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Update run table
                cursor.execute("""
                    UPDATE runs 
                    SET records_processed = ?, addresses_found = ?, success_rate = ?
                    WHERE run_id = ?
                """, (records_processed, addresses_found, 
                      (addresses_found / records_processed * 100) if records_processed > 0 else 0, run_id))
                
                # Insert process log
                cursor.execute("""
                    INSERT INTO process_logs (run_id, timestamp, stage, message, records_processed, 
                                            addresses_found, progress_percentage)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (run_id, datetime.now(), stage, message, records_processed, 
                      addresses_found, progress_percentage))
                
                conn.commit()
                return True
        except Exception as e:
            print(f"Error updating run progress: {e}")
            return False
    
    def complete_run(self, run_id: str, status: str = 'completed', error_message: str = None) -> bool:
        """Mark a run as completed."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE runs 
                    SET end_time = ?, status = ?, error_message = ?
                    WHERE run_id = ?
                """, (datetime.now(), status, error_message, run_id))
                conn.commit()
                return True
        except Exception as e:
            print(f"Error completing run: {e}")
            return False
    
    def save_results(self, run_id: str, results_df: pd.DataFrame) -> bool:
        """Save results for a run."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Clear existing results for this run
                cursor.execute("DELETE FROM results WHERE run_id = ?", (run_id,))
                
                # Insert new results
                for _, row in results_df.iterrows():
                    cursor.execute("""
                        INSERT INTO results (run_id, file_no, grantor, grantee, instrument_type,
                                           recording_date, film_code, legal_description, property_address, source)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (run_id, row.get('FileNo', ''), row.get('Grantor', ''), row.get('Grantee', ''),
                          row.get('Instrument Type', ''), row.get('Recording Date', ''), 
                          row.get('Film Code', ''), row.get('Legal Description', ''),
                          row.get('Property Address', ''), 'PDF extraction'))
                
                conn.commit()
                return True
        except Exception as e:
            print(f"Error saving results: {e}")
            return False
    
    def get_run_history(self, limit: int = 50) -> pd.DataFrame:
        """Get run history."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = """
                    SELECT run_id, start_time, end_time, status, total_records, records_processed,
                           addresses_found, success_rate, instrument_types, date_range, error_message
                    FROM runs 
                    ORDER BY start_time DESC 
                    LIMIT ?
                """
                return pd.read_sql_query(query, conn, params=(limit,))
        except Exception as e:
            print(f"Error getting run history: {e}")
            return pd.DataFrame()
    
    def get_run_details(self, run_id: str) -> Optional[Dict]:
        """Get detailed information about a specific run."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get run info
                cursor.execute("SELECT * FROM runs WHERE run_id = ?", (run_id,))
                run_data = cursor.fetchone()
                
                if not run_data:
                    return None
                
                # Get process logs
                cursor.execute("""
                    SELECT timestamp, stage, message, records_processed, addresses_found, progress_percentage
                    FROM process_logs 
                    WHERE run_id = ? 
                    ORDER BY timestamp
                """, (run_id,))
                logs = cursor.fetchall()
                
                # Get results
                cursor.execute("SELECT * FROM results WHERE run_id = ?", (run_id,))
                results = cursor.fetchall()
                
                return {
                    'run_info': run_data,
                    'process_logs': logs,
                    'results': results
                }
        except Exception as e:
            print(f"Error getting run details: {e}")
            return None
    
    def get_current_runs(self) -> List[Dict]:
        """Get currently running processes."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT run_id, start_time, records_processed, addresses_found, 
                           success_rate, instrument_types, date_range
                    FROM runs 
                    WHERE status = 'running'
                    ORDER BY start_time DESC
                """)
                return cursor.fetchall()
        except Exception as e:
            print(f"Error getting current runs: {e}")
            return []
    
    def get_run_results(self, run_id: str) -> pd.DataFrame:
        """Get results for a specific run."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = """
                    SELECT file_no, grantor, grantee, instrument_type, recording_date,
                           film_code, legal_description, property_address
                    FROM results 
                    WHERE run_id = ?
                    ORDER BY created_at
                """
                return pd.read_sql_query(query, conn, params=(run_id,))
        except Exception as e:
            print(f"Error getting run results: {e}")
            return pd.DataFrame()
    
    def delete_run(self, run_id: str) -> bool:
        """Delete a run and all associated data."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM process_logs WHERE run_id = ?", (run_id,))
                cursor.execute("DELETE FROM results WHERE run_id = ?", (run_id,))
                cursor.execute("DELETE FROM runs WHERE run_id = ?", (run_id,))
                conn.commit()
                return True
        except Exception as e:
            print(f"Error deleting run: {e}")
            return False
