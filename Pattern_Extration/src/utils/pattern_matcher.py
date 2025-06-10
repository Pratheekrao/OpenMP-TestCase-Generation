import re
import logging
from typing import List, Dict, Pattern, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class PatternMatch:
    pattern_type: str
    matched_text: str
    line_number: int
    column_start: int
    column_end: int
    groups: List[str]

class OpenMPPatternMatcher:
    def __init__(self):
        self.compiled_patterns = self._compile_patterns()
    
    def _compile_patterns(self) -> Dict[str, Pattern]:
        """Compile regex patterns for OpenMP constructs"""
        patterns = {
            'pragma_omp': re.compile(r'#pragma\s+omp\s+([^\n]+)', re.IGNORECASE),
            'run_command': re.compile(r'//\s*RUN:\s*(.+)', re.MULTILINE),
            'check_pattern': re.compile(r'//\s*CHECK[^:]*:\s*(.+)', re.MULTILINE),
            'expected_error': re.compile(r'//\s*expected-error[^:]*:\s*(.+)', re.MULTILINE),
            'expected_warning': re.compile(r'//\s*expected-warning[^:]*:\s*(.+)', re.MULTILINE),
            'openmp_version': re.compile(r'-fopenmp-version=(\d+)', re.IGNORECASE),
            'runtime_call': re.compile(r'@(__kmpc_[a-zA-Z_]+|omp_[a-zA-Z_]+)'),
            'ir_instruction': re.compile(r'\b(call|invoke|alloca|load|store|br|ret|define|declare)\b'),
            'openmp_clause': re.compile(r'\b(private|shared|reduction|schedule|collapse|nowait)\b'),
        }
        return patterns
    
    def find_all_matches(self, content: str, pattern_types: Optional[List[str]] = None) -> List[PatternMatch]:
        """Find all pattern matches in content"""
        if pattern_types is None:
            pattern_types = list(self.compiled_patterns.keys())
        
        matches = []
        lines = content.splitlines()
        
        for pattern_type in pattern_types:
            if pattern_type not in self.compiled_patterns:
                continue
                
            pattern = self.compiled_patterns[pattern_type]
            
            for line_num, line in enumerate(lines, 1):
                for match in pattern.finditer(line):
                    pattern_match = PatternMatch(
                        pattern_type=pattern_type,
                        matched_text=match.group(0),
                        line_number=line_num,
                        column_start=match.start(),
                        column_end=match.end(),
                        groups=list(match.groups())
                    )
                    matches.append(pattern_match)
        
        return matches
    
    def extract_openmp_directives(self, content: str) -> List[Dict]:
        """Extract OpenMP directive information"""
        matches = self.find_all_matches(content, ['pragma_omp'])
        directives = []
        
        for match in matches:
            if match.groups:
                directive_text = match.groups[0].strip()
                parts = directive_text.split()
                
                directive_info = {
                    'name': parts[0] if parts else '',
                    'clauses': parts[1:] if len(parts) > 1 else [],
                    'line_number': match.line_number,
                    'column_start': match.column_start,
                    'full_text': match.matched_text
                }
                directives.append(directive_info)
        
        return directives
    
    def extract_test_commands(self, content: str) -> Dict[str, List[str]]:
        """Extract test-related commands and patterns"""
        result = {
            'run_commands': [],
            'check_patterns': [],
            'expected_errors': [],
            'expected_warnings': []
        }
        
        command_types = ['run_command', 'check_pattern', 'expected_error', 'expected_warning']
        matches = self.find_all_matches(content, command_types)
        
        for match in matches:
            if match.pattern_type == 'run_command':
                result['run_commands'].append(match.groups[0] if match.groups else '')
            elif match.pattern_type == 'check_pattern':
                result['check_patterns'].append(match.groups[0] if match.groups else '')
            elif match.pattern_type == 'expected_error':
                result['expected_errors'].append(match.groups[0] if match.groups else '')
            elif match.pattern_type == 'expected_warning':
                result['expected_warnings'].append(match.groups[0] if match.groups else '')
        
        return result
    
    def extract_ir_patterns(self, content: str) -> List[str]:
        """Extract LLVM IR patterns from CHECK lines"""
        check_matches = self.find_all_matches(content, ['check_pattern'])
        ir_patterns = []
        
        for match in check_matches:
            if match.groups:
                check_text = match.groups[0]
                ir_match = self.compiled_patterns['ir_instruction'].search(check_text)
                if ir_match:
                    ir_patterns.append(check_text)
        
        return ir_patterns
    
    def extract_runtime_calls(self, content: str) -> List[str]:
        """Extract OpenMP runtime function calls"""
        matches = self.find_all_matches(content, ['runtime_call'])
        return [match.groups[0] for match in matches if match.groups]
