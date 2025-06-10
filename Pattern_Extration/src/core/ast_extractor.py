import clang.cindex
import logging
from typing import Dict, List, Optional
from pathlib import Path

from ..database.models import ASTNode, OpenMPDirective, ParseError

logger = logging.getLogger(__name__)

class ASTExtractor:
    def __init__(self, clang_library_path: str, clang_args: List[str]):
        self.clang_args = clang_args
        self.setup_clang()
    
    def setup_clang(self):
        """Initialize Clang bindings"""
        try:
            # Don't set library path - it's already been handled in main.py validation
            # or we're using bundled libclang
            self.index = clang.cindex.Index.create()
            logger.info("Clang AST extractor initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Clang: {e}")
            raise
    
    def extract_patterns(self, file_path: Path) -> Dict:
        """Extract AST patterns from a source file"""
        try:
            tu = self.index.parse(str(file_path), args=self.clang_args)
            if not tu:
                logger.warning(f"Failed to parse {file_path}")
                return {}
            
            patterns = {
                'ast_nodes': [],
                'openmp_directives': [],
                'function_declarations': [],
                'variable_declarations': [],
                'includes': [],
                'macros': [],
                'parse_errors': []  # Track parse errors as part of the pattern
            }
            
            # Handle parsing diagnostics and extract error patterns
            error_count = 0
            warning_count = 0
            
            if tu.diagnostics:
                for diag in tu.diagnostics:
                    parse_error = ParseError(
                        error_type=self._classify_diagnostic_type(diag.spelling),
                        message=diag.spelling,
                        line_number=diag.location.line if diag.location else 0,
                        column_number=diag.location.column if diag.location else 0,
                        severity=str(diag.severity)
                    )
                    patterns['parse_errors'].append(parse_error)
                    
                    if diag.severity >= clang.cindex.Diagnostic.Error:
                        error_count += 1
                    elif diag.severity >= clang.cindex.Diagnostic.Warning:
                        warning_count += 1
            
            # Log appropriately based on error count
            if error_count > 10:
                logger.warning(f"Many parse errors in {file_path.name} ({error_count} errors)")
            elif error_count > 0:
                logger.debug(f"Parse errors in {file_path.name} ({error_count} errors) - likely a negative test case")
            
            # Continue with AST traversal even if there are errors
            try:
                self._traverse_ast(tu.cursor, patterns)
            except Exception as e:
                logger.debug(f"AST traversal error in {file_path}: {e}")
            
            return patterns
            
        except Exception as e:
            logger.error(f"Error extracting AST patterns from {file_path}: {e}")
            return {}
    
    def _classify_diagnostic_type(self, message: str) -> str:
        """Classify the type of diagnostic message"""
        message_lower = message.lower()
        
        if 'expected' in message_lower and ('(' in message_lower or ')' in message_lower):
            return 'syntax_error'
        elif 'openmp' in message_lower and 'clause' in message_lower:
            return 'openmp_clause_error'
        elif 'directive' in message_lower and 'cannot contain' in message_lower:
            return 'directive_constraint_error'
        elif 'does not refer to a value' in message_lower:
            return 'reference_error'
        elif 'undeclared' in message_lower or 'not declared' in message_lower:
            return 'declaration_error'
        elif 'semantic' in message_lower or 'type' in message_lower:
            return 'semantic_error'
        else:
            return 'other_error'
    
    def _traverse_ast(self, node, patterns, depth=0):
        """Recursively traverse AST and extract patterns"""
        if depth > 100:  # Prevent infinite recursion
            return
        
        try:
            # Extract basic node information
            node_info = ASTNode(
                node_type=str(node.kind),
                spelling=node.spelling or "",
                location=f"{node.location.line}:{node.location.column}",
                children_count=len(list(node.get_children())),
                has_openmp=self._contains_openmp(node)
            )
            patterns['ast_nodes'].append(node_info)
            
            # Extract specific node types
            if node.kind == clang.cindex.CursorKind.FUNCTION_DECL:
                self._extract_function_declaration(node, patterns)
            elif node.kind == clang.cindex.CursorKind.VAR_DECL:
                self._extract_variable_declaration(node, patterns)
            elif node.kind == clang.cindex.CursorKind.INCLUSION_DIRECTIVE:
                self._extract_include(node, patterns)
            
            # Look for OpenMP pragmas in comments and attributes
            self._extract_openmp_pragmas(node, patterns)
            
            # Recursively process children
            for child in node.get_children():
                self._traverse_ast(child, patterns, depth + 1)
                
        except Exception as e:
            logger.debug(f"Error processing AST node: {e}")
    
    def _contains_openmp(self, node) -> bool:
        """Check if node contains OpenMP-related content"""
        try:
            if hasattr(node, 'spelling') and node.spelling:
                if 'omp' in node.spelling.lower():
                    return True
            
            # Check in comments and tokens
            if hasattr(node, 'get_tokens'):
                for token in node.get_tokens():
                    if 'omp' in token.spelling.lower():
                        return True
            
            return False
        except:
            return False
    
    def _extract_function_declaration(self, node, patterns):
        """Extract function declaration information"""
        func_info = {
            'name': node.spelling,
            'location': f"{node.location.line}:{node.location.column}",
            'return_type': node.result_type.spelling if node.result_type else "",
            'parameters': [],
            'has_openmp': self._contains_openmp(node)
        }
        
        # Extract parameters
        for child in node.get_children():
            if child.kind == clang.cindex.CursorKind.PARM_DECL:
                func_info['parameters'].append({
                    'name': child.spelling,
                    'type': child.type.spelling
                })
        
        patterns['function_declarations'].append(func_info)
    
    def _extract_variable_declaration(self, node, patterns):
        """Extract variable declaration information"""
        var_info = {
            'name': node.spelling,
            'type': node.type.spelling,
            'location': f"{node.location.line}:{node.location.column}",
            'is_global': node.semantic_parent.kind == clang.cindex.CursorKind.TRANSLATION_UNIT
        }
        patterns['variable_declarations'].append(var_info)
    
    def _extract_include(self, node, patterns):
        """Extract include directive information"""
        include_info = {
            'file': node.spelling,
            'location': f"{node.location.line}:{node.location.column}",
            'is_system': node.location.file.name.startswith('/usr/') if node.location.file else False
        }
        patterns['includes'].append(include_info)
    
    def _extract_openmp_pragmas(self, node, patterns):
        """Extract OpenMP pragma information from AST"""
        try:
            if hasattr(node, 'get_tokens'):
                tokens = list(node.get_tokens())
                for i, token in enumerate(tokens):
                    if (token.spelling == '#' and 
                        i + 1 < len(tokens) and 
                        tokens[i + 1].spelling == 'pragma' and
                        i + 2 < len(tokens) and
                        tokens[i + 2].spelling == 'omp'):
                        
                        # Extract the full pragma text
                        pragma_tokens = []
                        for j in range(i, len(tokens)):
                            if tokens[j].location.line != token.location.line:
                                break
                            pragma_tokens.append(tokens[j].spelling)
                        
                        pragma_text = ' '.join(pragma_tokens)
                        directive = self._parse_openmp_directive(pragma_text, token.location)
                        if directive:
                            patterns['openmp_directives'].append(directive)
                        
        except Exception as e:
            logger.debug(f"Error extracting OpenMP pragmas: {e}")
    
    def _parse_openmp_directive(self, pragma_text: str, location) -> Optional[OpenMPDirective]:
        """Parse OpenMP directive from pragma text"""
        try:
            # Simple parsing - can be enhanced
            parts = pragma_text.split()
            if len(parts) < 3 or parts[1] != 'pragma' or parts[2] != 'omp':
                return None
            
            directive_name = parts[3] if len(parts) > 3 else ""
            clauses = parts[4:] if len(parts) > 4 else []
            
            return OpenMPDirective(
                name=directive_name,
                clauses=clauses,
                line_number=location.line,
                column_number=location.column,
                full_text=pragma_text
            )
        except:
            return None
