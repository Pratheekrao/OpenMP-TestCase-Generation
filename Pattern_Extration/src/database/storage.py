import sqlite3
import json
import logging
from typing import List, Dict, Optional
from pathlib import Path
from datetime import datetime

from .models import TestPattern, CompilerStage, TestCategory

logger = logging.getLogger(__name__)

class PatternDatabase:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.setup_database()
    
    def setup_database(self):
        """Initialize SQLite database with proper schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Main patterns table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS test_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT UNIQUE NOT NULL,
                file_name TEXT NOT NULL,
                file_size INTEGER,
                compiler_stage TEXT NOT NULL,
                test_category TEXT NOT NULL,
                openmp_version TEXT,
                complexity_score INTEGER,
                line_count INTEGER,
                is_negative_test BOOLEAN,
                error_count INTEGER,
                created_timestamp TEXT,
                pattern_data TEXT NOT NULL
            )
        ''')
        
        # OpenMP directives table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS openmp_directives (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern_id INTEGER,
                directive_name TEXT NOT NULL,
                clauses TEXT,
                line_number INTEGER,
                column_number INTEGER,
                full_text TEXT,
                FOREIGN KEY (pattern_id) REFERENCES test_patterns (id)
            )
        ''')
        
        # Parse errors table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS parse_errors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern_id INTEGER,
                error_type TEXT NOT NULL,
                message TEXT NOT NULL,
                line_number INTEGER,
                column_number INTEGER,
                severity TEXT,
                FOREIGN KEY (pattern_id) REFERENCES test_patterns (id)
            )
        ''')
        
        # Expected error patterns table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS expected_error_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern_id INTEGER,
                pattern TEXT NOT NULL,
                error_category TEXT,
                regex_pattern TEXT,
                line_number INTEGER,
                FOREIGN KEY (pattern_id) REFERENCES test_patterns (id)
            )
        ''')
        
        # AST nodes table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ast_nodes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern_id INTEGER,
                node_type TEXT NOT NULL,
                spelling TEXT,
                location TEXT,
                children_count INTEGER,
                has_openmp BOOLEAN,
                FOREIGN KEY (pattern_id) REFERENCES test_patterns (id)
            )
        ''')
        
        # Create indexes for better query performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_compiler_stage ON test_patterns(compiler_stage)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_test_category ON test_patterns(test_category)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_negative_test ON test_patterns(is_negative_test)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_directive_name ON openmp_directives(directive_name)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_error_type ON parse_errors(error_type)')
        
        conn.commit()
        conn.close()
        logger.info(f"Database initialized at {self.db_path}")
    
    def store_pattern(self, pattern: TestPattern) -> bool:
        """Store a test pattern in the database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Insert main pattern
            cursor.execute('''
                INSERT OR REPLACE INTO test_patterns (
                    file_path, file_name, file_size, compiler_stage, test_category,
                    openmp_version, complexity_score, line_count, is_negative_test,
                    error_count, created_timestamp, pattern_data
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                pattern.file_path,
                pattern.file_name,
                pattern.file_size,
                pattern.compiler_stage.value,
                pattern.test_category.value,
                pattern.openmp_version,
                pattern.complexity_score,
                pattern.line_count,
                pattern.negative_test_characteristics.is_negative_test,
                len(pattern.parse_errors),
                pattern.created_timestamp,
                json.dumps(pattern.to_dict())
            ))
            
            pattern_id = cursor.lastrowid
            
            # Clear existing related data
            cursor.execute('DELETE FROM openmp_directives WHERE pattern_id = ?', (pattern_id,))
            cursor.execute('DELETE FROM parse_errors WHERE pattern_id = ?', (pattern_id,))
            cursor.execute('DELETE FROM expected_error_patterns WHERE pattern_id = ?', (pattern_id,))
            cursor.execute('DELETE FROM ast_nodes WHERE pattern_id = ?', (pattern_id,))
            
            # Insert OpenMP directives
            for directive in pattern.openmp_directives:
                cursor.execute('''
                    INSERT INTO openmp_directives (
                        pattern_id, directive_name, clauses, line_number, 
                        column_number, full_text
                    ) VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    pattern_id,
                    directive.name,
                    json.dumps(directive.clauses),
                    directive.line_number,
                    directive.column_number,
                    directive.full_text
                ))
            
            # Insert parse errors
            for error in pattern.parse_errors:
                cursor.execute('''
                    INSERT INTO parse_errors (
                        pattern_id, error_type, message, line_number,
                        column_number, severity
                    ) VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    pattern_id,
                    error.error_type,
                    error.message,
                    error.line_number,
                    error.column_number,
                    error.severity
                ))
            
            # Insert expected error patterns
            for expected in pattern.expected_error_patterns:
                cursor.execute('''
                    INSERT INTO expected_error_patterns (
                        pattern_id, pattern, error_category, regex_pattern, line_number
                    ) VALUES (?, ?, ?, ?, ?)
                ''', (
                    pattern_id,
                    expected.pattern,
                    expected.error_category,
                    expected.regex_pattern,
                    expected.line_number
                ))
            
            # Insert AST nodes
            for node in pattern.ast_nodes:
                cursor.execute('''
                    INSERT INTO ast_nodes (
                        pattern_id, node_type, spelling, location, 
                        children_count, has_openmp
                    ) VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    pattern_id,
                    node.node_type,
                    node.spelling,
                    node.location,
                    node.children_count,
                    node.has_openmp
                ))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Error storing pattern for {pattern.file_path}: {e}")
            return False
    
    def get_patterns_by_stage(self, stage: CompilerStage) -> List[TestPattern]:
        """Retrieve patterns by compiler stage"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            'SELECT pattern_data FROM test_patterns WHERE compiler_stage = ?',
            (stage.value,)
        )
        
        patterns = []
        for row in cursor.fetchall():
            pattern_dict = json.loads(row[0])
            patterns.append(TestPattern.from_dict(pattern_dict))
        
        conn.close()
        return patterns
    
    def get_negative_test_patterns(self) -> List[TestPattern]:
        """Retrieve all negative test patterns"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            'SELECT pattern_data FROM test_patterns WHERE is_negative_test = 1'
        )
        
        patterns = []
        for row in cursor.fetchall():
            pattern_dict = json.loads(row[0])
            patterns.append(TestPattern.from_dict(pattern_dict))
        
        conn.close()
        return patterns
    
    def get_error_patterns_by_type(self, error_type: str) -> List[Dict]:
        """Retrieve error patterns by error type"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT pe.*, tp.file_name 
            FROM parse_errors pe
            JOIN test_patterns tp ON pe.pattern_id = tp.id
            WHERE pe.error_type = ?
        ''', (error_type,))
        
        results = []
        for row in cursor.fetchall():
            results.append({
                'error_type': row[2],
                'message': row[3],
                'line_number': row[4],
                'severity': row[6],
                'file_name': row[7]
            })
        
        conn.close()
        return results
    
    def get_statistics(self) -> Dict:
        """Get database statistics including error patterns"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        stats = {}
        
        # Total patterns
        cursor.execute('SELECT COUNT(*) FROM test_patterns')
        stats['total_patterns'] = cursor.fetchone()[0]
        
        # Negative test patterns
        cursor.execute('SELECT COUNT(*) FROM test_patterns WHERE is_negative_test = 1')
        stats['negative_test_patterns'] = cursor.fetchone()[0]
        
        # By compiler stage
        cursor.execute('''
            SELECT compiler_stage, COUNT(*) 
            FROM test_patterns 
            GROUP BY compiler_stage
        ''')
        stats['by_stage'] = dict(cursor.fetchall())
        
        # By category
        cursor.execute('''
            SELECT test_category, COUNT(*) 
            FROM test_patterns 
            GROUP BY test_category
        ''')
        stats['by_category'] = dict(cursor.fetchall())
        
        # Most common directives
        cursor.execute('''
            SELECT directive_name, COUNT(*) 
            FROM openmp_directives 
            GROUP BY directive_name 
            ORDER BY COUNT(*) DESC 
            LIMIT 10
        ''')
        stats['top_directives'] = dict(cursor.fetchall())
        
        # Error statistics
        cursor.execute('''
            SELECT error_type, COUNT(*) 
            FROM parse_errors 
            GROUP BY error_type 
            ORDER BY COUNT(*) DESC
        ''')
        stats['error_types'] = dict(cursor.fetchall())
        
        # Total errors
        cursor.execute('SELECT COUNT(*) FROM parse_errors')
        stats['total_parse_errors'] = cursor.fetchone()[0]
        
        conn.close()
        return stats
    
    def export_to_json(self, output_path: str) -> bool:
        """Export all patterns to JSON file"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT pattern_data FROM test_patterns')
            
            patterns = []
            for row in cursor.fetchall():
                patterns.append(json.loads(row[0]))
            
            with open(output_path, 'w') as f:
                json.dump({
                    'metadata': {
                        'total_patterns': len(patterns),
                        'export_timestamp': datetime.now().isoformat(),
                        'database_path': self.db_path
                    },
                    'patterns': patterns
                }, f, indent=2)
            
            conn.close()
            logger.info(f"Exported {len(patterns)} patterns to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting to JSON: {e}")
            return False
