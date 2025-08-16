import sqlite3
import json
import time
import traceback
from datetime import datetime
from functools import wraps
from typing import Any, Dict, Optional, List, Callable
import streamlit as st
import os

class AuditLogger:
    def __init__(self, db_path: str = "audit_log.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the audit log database with required tables."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create audit_logs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                user_id TEXT NOT NULL,
                customer_id TEXT NOT NULL,
                operation_type TEXT NOT NULL,
                resource_type TEXT NOT NULL,
                resource_id TEXT,
                function_name TEXT NOT NULL,
                parameters TEXT,
                result_status TEXT,
                result_data TEXT,
                error_message TEXT,
                error_type TEXT,
                error_code TEXT,
                stack_trace TEXT,
                execution_time_ms INTEGER,
                session_id TEXT
            )
        ''')
        
        # Add new columns to existing table if they don't exist
        try:
            cursor.execute('ALTER TABLE audit_logs ADD COLUMN error_type TEXT')
        except sqlite3.OperationalError:
            pass  # Column already exists
        
        try:
            cursor.execute('ALTER TABLE audit_logs ADD COLUMN error_code TEXT')
        except sqlite3.OperationalError:
            pass  # Column already exists
            
        try:
            cursor.execute('ALTER TABLE audit_logs ADD COLUMN stack_trace TEXT')
        except sqlite3.OperationalError:
            pass  # Column already exists
        
        # Create indexes for better performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON audit_logs(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_id ON audit_logs(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_customer_id ON audit_logs(customer_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_operation_type ON audit_logs(operation_type)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_resource_type ON audit_logs(resource_type)')
        
        conn.commit()
        conn.close()
    
    def get_user_id(self) -> str:
        """Get current user ID from Streamlit session state or environment."""
        if 'user_id' in st.session_state:
            return st.session_state.user_id
        elif os.getenv('GOOGLE_ADS_USER_ID'):
            return os.getenv('GOOGLE_ADS_USER_ID')
        else:
            # Generate a session-based user ID if none exists
            if 'generated_user_id' not in st.session_state:
                st.session_state.generated_user_id = f"user_{int(time.time())}"
            return st.session_state.generated_user_id
    
    def get_customer_id(self) -> str:
        """Get customer ID from Streamlit session state."""
        return st.session_state.get('customer_id', 'unknown')
    
    def get_session_id(self) -> str:
        """Get session ID for tracking related operations."""
        if 'session_id' not in st.session_state:
            st.session_state.session_id = f"session_{int(time.time())}"
        return st.session_state.session_id
    
    def log_operation(self, 
                     operation_type: str,
                     resource_type: str,
                     function_name: str,
                     parameters: Dict[str, Any] = None,
                     resource_id: str = None,
                     result_status: str = "SUCCESS",
                     result_data: Any = None,
                     error_message: str = None,
                     error_type: str = None,
                     error_code: str = None,
                     stack_trace: str = None,
                     execution_time_ms: int = None):
        """Log an operation to the audit database."""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO audit_logs (
                    user_id, customer_id, operation_type, resource_type,
                    resource_id, function_name, parameters, result_status,
                    result_data, error_message, error_type, error_code,
                    stack_trace, execution_time_ms, session_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                self.get_user_id(),
                self.get_customer_id(),
                operation_type,
                resource_type,
                resource_id,
                function_name,
                json.dumps(parameters) if parameters else None,
                result_status,
                json.dumps(result_data) if result_data else None,
                error_message,
                error_type,
                error_code,
                stack_trace,
                execution_time_ms,
                self.get_session_id()
            ))
            
            conn.commit()
        except Exception as e:
            print(f"Error logging audit entry: {e}")
        finally:
            conn.close()
    
    def get_audit_logs(self, 
                      limit: int = 100,
                      user_id: str = None,
                      customer_id: str = None,
                      operation_type: str = None,
                      resource_type: str = None,
                      start_date: str = None,
                      end_date: str = None) -> List[Dict]:
        """Retrieve audit logs with optional filtering."""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = "SELECT * FROM audit_logs WHERE 1=1"
        params = []
        
        if user_id:
            query += " AND user_id = ?"
            params.append(user_id)
        
        if customer_id:
            query += " AND customer_id = ?"
            params.append(customer_id)
        
        if operation_type:
            query += " AND operation_type = ?"
            params.append(operation_type)
        
        if resource_type:
            query += " AND resource_type = ?"
            params.append(resource_type)
        
        if start_date:
            query += " AND timestamp >= ?"
            params.append(start_date)
        
        if end_date:
            query += " AND timestamp <= ?"
            params.append(end_date)
        
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        
        columns = [description[0] for description in cursor.description]
        results = []
        
        for row in cursor.fetchall():
            log_entry = dict(zip(columns, row))
            # Parse JSON fields
            if log_entry['parameters']:
                try:
                    log_entry['parameters'] = json.loads(log_entry['parameters'])
                except json.JSONDecodeError:
                    pass
            
            if log_entry['result_data']:
                try:
                    log_entry['result_data'] = json.loads(log_entry['result_data'])
                except json.JSONDecodeError:
                    pass
            
            results.append(log_entry)
        
        conn.close()
        return results
    
    def log_error(self, 
                  operation_type: str,
                  resource_type: str,
                  function_name: str,
                  error: Exception,
                  parameters: Dict[str, Any] = None,
                  resource_id: str = None,
                  execution_time_ms: int = None):
        """Helper method to manually log errors with detailed information."""
        
        # Extract detailed error information
        error_type = type(error).__name__
        error_code = None
        error_message = str(error)
        stack_trace = traceback.format_exc()
        
        # Try to extract Google Ads API specific error details
        if hasattr(error, 'failure') and hasattr(error.failure, 'errors'):
            # Google Ads API exception
            errors = []
            for err in error.failure.errors:
                error_info = {
                    'error_code': getattr(err, 'error_code', {}).get('name', 'UNKNOWN'),
                    'message': getattr(err, 'message', str(err)),
                    'location': getattr(err, 'location', None)
                }
                errors.append(error_info)
                if error_code is None:  # Use the first error code
                    error_code = error_info['error_code']
            
            error_message = f"Google Ads API Error: {json.dumps(errors)}"
        elif hasattr(error, 'code'):
            # HTTP or other errors with codes
            error_code = str(error.code)
        
        self.log_operation(
            operation_type=operation_type,
            resource_type=resource_type,
            function_name=function_name,
            parameters=parameters,
            resource_id=resource_id,
            result_status="ERROR",
            error_message=error_message,
            error_type=error_type,
            error_code=error_code,
            stack_trace=stack_trace,
            execution_time_ms=execution_time_ms
        )
    
    def get_operation_stats(self) -> Dict[str, Any]:
        """Get statistics about operations for dashboard."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        stats = {}
        
        # Total operations
        cursor.execute("SELECT COUNT(*) FROM audit_logs")
        stats['total_operations'] = cursor.fetchone()[0]
        
        # Operations by type
        cursor.execute("""
            SELECT operation_type, COUNT(*) as count 
            FROM audit_logs 
            GROUP BY operation_type 
            ORDER BY count DESC
        """)
        stats['operations_by_type'] = dict(cursor.fetchall())
        
        # Operations by resource type
        cursor.execute("""
            SELECT resource_type, COUNT(*) as count 
            FROM audit_logs 
            GROUP BY resource_type 
            ORDER BY count DESC
        """)
        stats['operations_by_resource'] = dict(cursor.fetchall())
        
        # Success/failure rates
        cursor.execute("""
            SELECT result_status, COUNT(*) as count 
            FROM audit_logs 
            GROUP BY result_status
        """)
        stats['status_breakdown'] = dict(cursor.fetchall())
        
        # Recent activity (last 24 hours)
        cursor.execute("""
            SELECT COUNT(*) FROM audit_logs 
            WHERE timestamp >= datetime('now', '-1 day')
        """)
        stats['operations_last_24h'] = cursor.fetchone()[0]
        
        # Most active users
        cursor.execute("""
            SELECT user_id, COUNT(*) as count 
            FROM audit_logs 
            GROUP BY user_id 
            ORDER BY count DESC 
            LIMIT 10
        """)
        stats['most_active_users'] = dict(cursor.fetchall())
        
        # Error statistics
        cursor.execute("""
            SELECT error_type, COUNT(*) as count 
            FROM audit_logs 
            WHERE result_status = 'ERROR' AND error_type IS NOT NULL
            GROUP BY error_type 
            ORDER BY count DESC
        """)
        stats['errors_by_type'] = dict(cursor.fetchall())
        
        cursor.execute("""
            SELECT error_code, COUNT(*) as count 
            FROM audit_logs 
            WHERE result_status = 'ERROR' AND error_code IS NOT NULL
            GROUP BY error_code 
            ORDER BY count DESC
            LIMIT 10
        """)
        stats['top_error_codes'] = dict(cursor.fetchall())
        
        # Recent errors (last 24 hours)
        cursor.execute("""
            SELECT COUNT(*) FROM audit_logs 
            WHERE result_status = 'ERROR' AND timestamp >= datetime('now', '-1 day')
        """)
        stats['errors_last_24h'] = cursor.fetchone()[0]
        
        conn.close()
        return stats

# Global audit logger instance
audit_logger = AuditLogger()

def audit_log(operation_type: str, resource_type: str):
    """Decorator to automatically log function calls."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            
            # Extract parameters for logging (exclude sensitive data)
            log_params = {}
            if args:
                log_params['args_count'] = len(args)
            if kwargs:
                # Filter out sensitive parameters
                filtered_kwargs = {k: v for k, v in kwargs.items() 
                                 if k not in ['client', 'service', 'password', 'token']}
                log_params.update(filtered_kwargs)
            
            try:
                result = func(*args, **kwargs)
                execution_time = int((time.time() - start_time) * 1000)
                
                # Extract resource ID from result if possible
                resource_id = None
                if hasattr(result, 'results') and result.results:
                    if hasattr(result.results[0], 'resource_name'):
                        resource_id = result.results[0].resource_name
                elif isinstance(result, str) and '/' in result:
                    resource_id = result
                
                audit_logger.log_operation(
                    operation_type=operation_type,
                    resource_type=resource_type,
                    function_name=func.__name__,
                    parameters=log_params,
                    resource_id=resource_id,
                    result_status="SUCCESS",
                    result_data={"resource_count": len(result.results) if hasattr(result, 'results') else None},
                    execution_time_ms=execution_time
                )
                
                return result
                
            except Exception as e:
                execution_time = int((time.time() - start_time) * 1000)
                
                # Extract detailed error information
                error_type = type(e).__name__
                error_code = None
                error_message = str(e)
                stack_trace = traceback.format_exc()
                
                # Try to extract Google Ads API specific error details
                if hasattr(e, 'failure') and hasattr(e.failure, 'errors'):
                    # Google Ads API exception
                    errors = []
                    for error in e.failure.errors:
                        error_info = {
                            'error_code': getattr(error, 'error_code', {}).get('name', 'UNKNOWN'),
                            'message': getattr(error, 'message', str(error)),
                            'location': getattr(error, 'location', None)
                        }
                        errors.append(error_info)
                        if error_code is None:  # Use the first error code
                            error_code = error_info['error_code']
                    
                    error_message = f"Google Ads API Error: {json.dumps(errors)}"
                elif hasattr(e, 'code'):
                    # HTTP or other errors with codes
                    error_code = str(e.code)
                
                audit_logger.log_operation(
                    operation_type=operation_type,
                    resource_type=resource_type,
                    function_name=func.__name__,
                    parameters=log_params,
                    result_status="ERROR",
                    error_message=error_message,
                    error_type=error_type,
                    error_code=error_code,
                    stack_trace=stack_trace,
                    execution_time_ms=execution_time
                )
                
                raise e
        
        return wrapper
    return decorator