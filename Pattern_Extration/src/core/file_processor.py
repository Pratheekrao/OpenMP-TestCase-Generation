import re
import logging
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

from ..database.models import (
    TestPattern, CompilerStage, TestCategory, OpenMPDirective,
    ExpectedErrorPattern, NegativeTestCharacteristics
)
from .ast_extractor import ASTExtractor

logger = logging.getLogger(__name__)

class FileProcessor:
    def __init__(self, ast_extractor: ASTExtractor):
        self.ast_extractor = ast_extractor
    
    def process_test_file(self, file_path: Path) -> Optional[TestPattern]:
        """Process a single test file and extract all patterns"""
        try:
            if not file_path.exists():
                logger.warning(f"File does not exist: {file_path}")
                return None
            
            content = self._read_file_content(file_path)
            if not content:
                return None
            
            # Extract basic file information
            file_info = self._extract_file_info(file_path, content)
            
            # Extract test structure patterns
            run_commands = self._extract_run_commands(content)
            compiler_flags = self._extract_compiler_flags(run_commands)
            compiler_stage = self._determine_compiler_stage(run_commands, content)
            
            # Extract OpenMP-specific patterns
            openmp_directives = self._extract_openmp_directives(content)
            openmp_version = self._extract_openmp_version(content, run_commands)
            
            # Extract test validation patterns
            check_patterns = self._extract_check_patterns(content)
            expected_errors = self._extract_expected_errors(content)
            expected_warnings = self._extract_expected_warnings(content)
            
            # Extract AST patterns (including parse errors)
            ast_patterns = self.ast_extractor.extract_patterns(file_path)
            
            # Extract and categorize error patterns
            error_patterns = self._categorize_error_patterns(
                ast_patterns.get('parse_errors', []), 
                expected_errors, 
                content
            )
            
            # Extract negative test characteristics
            negative_test_info = self._extract_negative_test_characteristics(
                file_path, content, error_patterns
            )
            
            # Extract IR patterns (for CodeGen tests)
            ir_patterns = self._extract_ir_patterns(check_patterns)
            runtime_calls = self._extract_runtime_calls(check_patterns)
            
            # Categorize and score the test
            test_category = self._categorize_test(file_path.name, openmp_directives, content)
            complexity_score = self._calculate_complexity_score(
                openmp_directives, check_patterns, expected_errors, ast_patterns, error_patterns
            )
            
            # Create the test pattern
            pattern = TestPattern(
                # File Information
                file_path=str(file_path),
                file_name=file_path.name,
                file_size=file_info['size'],
                
                # Compiler Stage Information
                compiler_stage=compiler_stage,
                run_commands=run_commands,
                compiler_flags=compiler_flags,
                
                # OpenMP Information
                openmp_directives=openmp_directives,
                openmp_version=openmp_version,
                
                # Test Structure
                test_category=test_category,
                check_patterns=check_patterns,
                expected_errors=expected_errors,
                expected_warnings=expected_warnings,
                
                # AST Information
                ast_nodes=ast_patterns.get('ast_nodes', []),
                function_declarations=[str(f) for f in ast_patterns.get('function_declarations', [])],
                variable_declarations=[str(v) for v in ast_patterns.get('variable_declarations', [])],
                
                # IR Patterns
                ir_patterns=ir_patterns,
                runtime_calls=runtime_calls,
                
                # Error Pattern Information
                parse_errors=error_patterns['parse_errors'],
                expected_error_patterns=error_patterns['expected_patterns'],
                negative_test_characteristics=negative_test_info,
                error_trigger_mechanisms=error_patterns['trigger_mechanisms'],
                error_types=list(error_patterns['error_types']),
                
                # Metadata
                complexity_score=complexity_score,
                line_count=file_info['line_count'],
                created_timestamp=datetime.now().isoformat()
            )
            
            return pattern
            
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}")
            return None
    
    def _categorize_error_patterns(self, parse_errors: List, 
                                  expected_errors: List[str], 
                                  content: str) -> Dict:
        """Categorize and analyze error patterns"""
        error_patterns = {
            'parse_errors': parse_errors,  # Already ParseError objects
            'expected_patterns': [],
            'trigger_mechanisms': [],
            'error_types': set()
        }
        
        # Add error types from parse errors
        for error in parse_errors:
            error_patterns['error_types'].add(error.error_type)
        
        # Analyze expected error patterns
        lines = content.splitlines()
        for i, line in enumerate(lines, 1):
            for expected in expected_errors:
                if expected in line:
                    pattern_info = ExpectedErrorPattern(
                        pattern=expected,
                        error_category=self._classify_expected_error(expected),
                        regex_pattern=self._extract_regex_pattern(expected),
                        line_number=i
                    )
                    error_patterns['expected_patterns'].append(pattern_info)
        
        # Extract error trigger mechanisms
        error_patterns['trigger_mechanisms'] = self._extract_error_triggers(content)
        
        return error_patterns
    
    def _classify_expected_error(self, expected_error: str) -> str:
        """Classify the category of expected error"""
        error_lower = expected_error.lower()
        
        if 'clause' in error_lower:
            return 'clause_error'
        elif 'directive' in error_lower:
            return 'directive_error'
        elif 'syntax' in error_lower or 'expected' in error_lower:
            return 'syntax_error'
        elif 'semantic' in error_lower or 'type' in error_lower:
            return 'semantic_error'
        elif 'undeclared' in error_lower or 'undefined' in error_lower:
            return 'declaration_error'
        else:
            return 'general_error'
    
    def _extract_regex_pattern(self, expected_error: str) -> Optional[str]:
        """Extract regex pattern from expected error if present"""
        # Look for regex-like patterns in the expected error
        regex_match = re.search(r'\{\{.*?\}\}', expected_error)
        if regex_match:
            return regex_match.group(0)
        return None
    
    def _extract_negative_test_characteristics(self, file_path: Path, 
                                             content: str, 
                                             error_patterns: Dict) -> NegativeTestCharacteristics:
        """Extract characteristics specific to negative test cases"""
        is_negative = self._is_negative_test_case(file_path, content)
        
        characteristics = NegativeTestCharacteristics(
            is_negative_test=is_negative,
            error_testing_strategy=None,
            expected_vs_actual_errors={},
            error_coverage_areas=[],
            error_trigger_count=len(error_patterns['trigger_mechanisms'])
        )
        
        if is_negative:
            # Determine the error testing strategy
            filename = file_path.name.lower()
            if 'messages' in filename:
                characteristics.error_testing_strategy = 'error_message_validation'
            elif 'syntax' in filename:
                characteristics.error_testing_strategy = 'syntax_validation'
            elif 'semantic' in filename:
                characteristics.error_testing_strategy = 'semantic_validation'
            else:
                characteristics.error_testing_strategy = 'general_error_testing'
            
            # Map expected errors to actual parse errors
            characteristics.expected_vs_actual_errors = self._map_expected_to_actual_errors(
                error_patterns['expected_patterns'],
                error_patterns['parse_errors']
            )
            
            # Identify what areas of OpenMP are being tested for errors
            characteristics.error_coverage_areas = self._identify_error_coverage_areas(
                content, error_patterns
            )
        
        return characteristics
    
    def _map_expected_to_actual_errors(self, expected_patterns: List, 
                                     parse_errors: List) -> Dict:
        """Map expected error patterns to actual parse errors"""
        mapping = {
            'total_expected': len(expected_patterns),
            'total_actual': len(parse_errors),
            'matched_errors': [],
            'unmatched_expected': [],
            'unexpected_errors': []
        }
        
        # Simple mapping based on line numbers and error types
        expected_by_line = {p.line_number: p for p in expected_patterns}
        actual_by_line = {}
        
        for error in parse_errors:
            line = error.line_number
            if line not in actual_by_line:
                actual_by_line[line] = []
            actual_by_line[line].append(error)
        
        # Find matches
        for line, expected in expected_by_line.items():
            if line in actual_by_line:
                mapping['matched_errors'].append({
                    'line': line,
                    'expected': expected.pattern,
                    'actual': [e.message for e in actual_by_line[line]]
                })
            else:
                mapping['unmatched_expected'].append(expected.pattern)
        
        # Find unexpected errors
        for line, errors in actual_by_line.items():
            if line not in expected_by_line:
                mapping['unexpected_errors'].extend([e.message for e in errors])
        
        return mapping
    
    def _identify_error_coverage_areas(self, content: str, error_patterns: Dict) -> List[str]:
        """Identify what areas of OpenMP are being tested for errors"""
        coverage_areas = set()
        
        # Check for specific OpenMP constructs being tested
        openmp_constructs = [
            'parallel', 'for', 'sections', 'single', 'task', 'target',
            'teams', 'distribute', 'simd', 'atomic', 'critical', 'barrier'
        ]
        
        content_lower = content.lower()
        for construct in openmp_constructs:
            if construct in content_lower:
                coverage_areas.add(construct)
        
        # Check for clause testing
        openmp_clauses = [
            'private', 'shared', 'reduction', 'schedule', 'collapse',
            'nowait', 'ordered', 'default', 'copyin', 'copyprivate'
        ]
        
        for clause in openmp_clauses:
            if clause in content_lower:
                coverage_areas.add(f"{clause}_clause")
        
        return list(coverage_areas)
    
    def _extract_error_triggers(self, content: str) -> List[str]:
        """Extract mechanisms that trigger errors in the test"""
        triggers = []
        
        # Look for common error trigger patterns
        trigger_patterns = [
            (r'#pragma\s+omp\s+\w+.*?(?=\n)', 'openmp_directive'),
            (r'expected-error.*?"([^"]+)"', 'expected_error'),
            (r'expected-warning.*?"([^"]+)"', 'expected_warning'),
            (r'// ERROR:.*', 'error_comment'),
            (r'// FIXME:.*', 'fixme_comment')
        ]
        
        for pattern, trigger_type in trigger_patterns:
            matches = re.findall(pattern, content, re.MULTILINE | re.IGNORECASE)
            for match in matches:
                triggers.append(f"{trigger_type}: {match}")
        
        return triggers
    
    def _read_file_content(self, file_path: Path) -> Optional[str]:
        """Read file content with proper encoding handling"""
        try:
            return file_path.read_text(encoding='utf-8', errors='ignore')
        except Exception as e:
            logger.warning(f"Error reading {file_path}: {e}")
            return None
    
    def _extract_file_info(self, file_path: Path, content: str) -> Dict:
        """Extract basic file information"""
        return {
            'size': file_path.stat().st_size,
            'line_count': len(content.splitlines()),
            'extension': file_path.suffix
        }
    
    def _extract_run_commands(self, content: str) -> List[str]:
        """Extract RUN commands from test file"""
        run_pattern = r'//\s*RUN:\s*(.+)'
        matches = re.findall(run_pattern, content, re.MULTILINE)
        return [match.strip() for match in matches]
    
    def _extract_compiler_flags(self, run_commands: List[str]) -> List[str]:
        """Extract compiler flags from RUN commands"""
        flags = set()
        for cmd in run_commands:
            # Extract flags starting with -
            flag_matches = re.findall(r'(-[a-zA-Z0-9-]+)', cmd)
            flags.update(flag_matches)
        return list(flags)
    
    def _determine_compiler_stage(self, run_commands: List[str], content: str) -> CompilerStage:
        """Determine which compiler stage this test targets"""
        run_text = ' '.join(run_commands).lower()
        
        if '-fsyntax-only' in run_text or '-verify' in run_text:
            return CompilerStage.SEMA
        elif '-ast-print' in run_text or '-ast-dump' in run_text:
            return CompilerStage.AST_PRINT
        elif '-emit-llvm' in run_text or 'filecheck' in run_text:
            return CompilerStage.CODEGEN
        elif any('parse' in cmd.lower() for cmd in run_commands):
            return CompilerStage.PARSE
        else:
            return CompilerStage.UNKNOWN
    
    def _extract_openmp_directives(self, content: str) -> List[OpenMPDirective]:
        """Extract OpenMP directives from source code"""
        directives = []
        lines = content.splitlines()
        
        for line_num, line in enumerate(lines, 1):
            # Match OpenMP pragma directives
            pragma_match = re.match(r'\s*#pragma\s+omp\s+(.+)', line)
            if pragma_match:
                directive_text = pragma_match.group(1).strip()
                parts = directive_text.split()
                directive_name = parts[0] if parts else ""
                clauses = parts[1:] if len(parts) > 1 else []
                
                directive = OpenMPDirective(
                    name=directive_name,
                    clauses=clauses,
                    line_number=line_num,
                    column_number=line.find('#pragma'),
                    full_text=line.strip()
                )
                directives.append(directive)
        
        return directives
    
    def _extract_openmp_version(self, content: str, run_commands: List[str]) -> Optional[str]:
        """Extract OpenMP version from test file"""
        # Check run commands for version flags
        for cmd in run_commands:
            version_match = re.search(r'-fopenmp-version=(\d+)', cmd)
            if version_match:
                return version_match.group(1)
        
        # Check content for version comments
        version_match = re.search(r'OpenMP\s+(\d+\.\d+)', content, re.IGNORECASE)
        if version_match:
            return version_match.group(1)
        
        return None
    
    def _extract_check_patterns(self, content: str) -> List[str]:
        """Extract CHECK patterns for verification"""
        check_pattern = r'//\s*CHECK[^:]*:\s*(.+)'
        matches = re.findall(check_pattern, content, re.MULTILINE)
        return [match.strip() for match in matches]
    
    def _extract_expected_errors(self, content: str) -> List[str]:
        """Extract expected error patterns"""
        error_pattern = r'//\s*expected-error[^:]*:\s*(.+)'
        matches = re.findall(error_pattern, content, re.MULTILINE)
        return [match.strip() for match in matches]
    
    def _extract_expected_warnings(self, content: str) -> List[str]:
        """Extract expected warning patterns"""
        warning_pattern = r'//\s*expected-warning[^:]*:\s*(.+)'
        matches = re.findall(warning_pattern, content, re.MULTILINE)
        return [match.strip() for match in matches]
    
    def _extract_ir_patterns(self, check_patterns: List[str]) -> List[str]:
        """Extract LLVM IR patterns from CHECK lines"""
        ir_keywords = [
            'call', 'invoke', 'alloca', 'load', 'store', 'br', 'ret',
            'define', 'declare', 'getelementptr', 'bitcast', 'icmp'
        ]
        
        ir_patterns = []
        for pattern in check_patterns:
            if any(keyword in pattern.lower() for keyword in ir_keywords):
                ir_patterns.append(pattern)
        
        return ir_patterns
    
    def _extract_runtime_calls(self, check_patterns: List[str]) -> List[str]:
        """Extract OpenMP runtime function calls"""
        runtime_calls = []
        for pattern in check_patterns:
            # Look for OpenMP runtime function patterns
            runtime_match = re.search(r'@(__kmpc_[a-zA-Z_]+|omp_[a-zA-Z_]+)', pattern)
            if runtime_match:
                runtime_calls.append(runtime_match.group(1))
        
        return list(set(runtime_calls))  # Remove duplicates
    
    def _categorize_test(self, filename: str, directives: List[OpenMPDirective], content: str) -> TestCategory:
        """Categorize test based on filename, directives, and content"""
        filename_lower = filename.lower()
        content_lower = content.lower()
        directive_names = [d.name.lower() for d in directives]
        
        # Check for specific categories
        if ('parallel' in filename_lower or 
            any('parallel' in name for name in directive_names) or
            'parallel' in content_lower):
            return TestCategory.PARALLEL
        
        elif ('for' in filename_lower or 'sections' in filename_lower or
              any(name in ['for', 'sections', 'single'] for name in directive_names)):
            return TestCategory.WORKSHARING
        
        elif ('target' in filename_lower or 
              any('target' in name for name in directive_names)):
            return TestCategory.TARGET
        
        elif ('atomic' in filename_lower or 'critical' in filename_lower or
              any(name in ['atomic', 'critical', 'barrier'] for name in directive_names)):
            return TestCategory.SYNCHRONIZATION
        
        elif ('simd' in filename_lower or 
              any('simd' in name for name in directive_names)):
            return TestCategory.SIMD
        
        elif ('task' in filename_lower or 
              any('task' in name for name in directive_names)):
            return TestCategory.TASK
        
        else:
            return TestCategory.GENERAL
    
    def _is_negative_test_case(self, file_path: Path, content: str) -> bool:
        """Detect if this is a negative test case (expected to have errors)"""
        filename = file_path.name.lower()
        
        # Common patterns for negative test cases
        negative_indicators = [
            'messages', 'error', 'warn', 'diag', 'negative',
            'invalid', 'bad', 'fail', 'wrong'
        ]
        
        # Check filename
        if any(indicator in filename for indicator in negative_indicators):
            return True
        
        # Check for expected-error comments
        if 'expected-error' in content or 'expected-warning' in content:
            return True
        
        return False
    
    def _calculate_complexity_score(self, directives: List[OpenMPDirective], 
                                  check_patterns: List[str], 
                                  expected_errors: List[str],
                                  ast_patterns: Dict,
                                  error_patterns: Dict) -> int:
        """Calculate test complexity score (0-10)"""
        score = 0
        
        # Directive complexity
        score += len(directives) * 2
        
        # Clause complexity
        total_clauses = sum(len(d.clauses) for d in directives)
        score += total_clauses
        
        # Verification complexity
        score += len(check_patterns)
        score += len(expected_errors) * 2  # Errors are more complex
        
        # AST complexity
        score += len(ast_patterns.get('function_declarations', [])) // 2
        
        # Error pattern complexity
        score += len(error_patterns.get('parse_errors', []))
        score += len(error_patterns.get('error_types', set()))
        
        # Cap at 10
        return min(score, 10)
