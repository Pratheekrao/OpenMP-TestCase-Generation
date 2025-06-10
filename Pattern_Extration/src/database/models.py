from dataclasses import dataclass, asdict
from enum import Enum
from typing import List, Dict, Optional, Set
import json

class CompilerStage(Enum):
    PARSE = "parse"
    SEMA = "sema" 
    CODEGEN = "codegen"
    AST_PRINT = "ast_print"
    UNKNOWN = "unknown"

class TestCategory(Enum):
    PARALLEL = "parallel"
    WORKSHARING = "worksharing"
    TARGET = "target"
    SYNCHRONIZATION = "synchronization"
    SIMD = "simd"
    TASK = "task"
    GENERAL = "general"

class ErrorType(Enum):
    SYNTAX_ERROR = "syntax_error"
    OPENMP_CLAUSE_ERROR = "openmp_clause_error"
    DIRECTIVE_CONSTRAINT_ERROR = "directive_constraint_error"
    REFERENCE_ERROR = "reference_error"
    DECLARATION_ERROR = "declaration_error"
    SEMANTIC_ERROR = "semantic_error"
    OTHER_ERROR = "other_error"

@dataclass
class OpenMPDirective:
    name: str
    clauses: List[str]
    line_number: int
    column_number: int
    full_text: str

@dataclass
class ASTNode:
    node_type: str
    spelling: str
    location: str
    children_count: int
    has_openmp: bool

@dataclass
class ParseError:
    error_type: str
    message: str
    line_number: int
    column_number: int
    severity: str

@dataclass
class ExpectedErrorPattern:
    pattern: str
    error_category: str
    regex_pattern: Optional[str]
    line_number: int

@dataclass
class NegativeTestCharacteristics:
    is_negative_test: bool
    error_testing_strategy: Optional[str]
    expected_vs_actual_errors: Dict
    error_coverage_areas: List[str]
    error_trigger_count: int

@dataclass
class TestPattern:
    # File Information
    file_path: str
    file_name: str
    file_size: int
    
    # Compiler Stage Information
    compiler_stage: CompilerStage
    run_commands: List[str]
    compiler_flags: List[str]
    
    # OpenMP Information
    openmp_directives: List[OpenMPDirective]
    openmp_version: Optional[str]
    
    # Test Structure
    test_category: TestCategory
    check_patterns: List[str]
    expected_errors: List[str]
    expected_warnings: List[str]
    
    # AST Information
    ast_nodes: List[ASTNode]
    function_declarations: List[str]
    variable_declarations: List[str]
    
    # IR Patterns (for CodeGen tests)
    ir_patterns: List[str]
    runtime_calls: List[str]
    
    # Error Pattern Information
    parse_errors: List[ParseError]
    expected_error_patterns: List[ExpectedErrorPattern]
    negative_test_characteristics: NegativeTestCharacteristics
    error_trigger_mechanisms: List[str]
    error_types: List[str]
    
    # Metadata
    complexity_score: int
    line_count: int
    created_timestamp: str
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        result = asdict(self)
        # Convert enums to strings
        result['compiler_stage'] = self.compiler_stage.value
        result['test_category'] = self.test_category.value
        return result
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'TestPattern':
        """Create from dictionary"""
        # Convert string enums back
        data['compiler_stage'] = CompilerStage(data['compiler_stage'])
        data['test_category'] = TestCategory(data['test_category'])
        
        # Convert directive dicts back to objects
        data['openmp_directives'] = [
            OpenMPDirective(**d) if isinstance(d, dict) else d 
            for d in data['openmp_directives']
        ]
        
        # Convert AST node dicts back to objects
        data['ast_nodes'] = [
            ASTNode(**n) if isinstance(n, dict) else n 
            for n in data['ast_nodes']
        ]
        
        # Convert error pattern dicts back to objects
        data['parse_errors'] = [
            ParseError(**e) if isinstance(e, dict) else e 
            for e in data['parse_errors']
        ]
        
        data['expected_error_patterns'] = [
            ExpectedErrorPattern(**p) if isinstance(p, dict) else p 
            for p in data['expected_error_patterns']
        ]
        
        data['negative_test_characteristics'] = (
            NegativeTestCharacteristics(**data['negative_test_characteristics'])
            if isinstance(data['negative_test_characteristics'], dict)
            else data['negative_test_characteristics']
        )
        
        return cls(**data)
