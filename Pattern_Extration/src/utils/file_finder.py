import logging
from pathlib import Path
from typing import List, Set
import fnmatch

logger = logging.getLogger(__name__)

class OpenMPFileFinder:
    def __init__(self, base_dir: str, patterns: List[str], extensions: List[str]):
        self.base_dir = Path(base_dir)
        self.patterns = patterns
        self.extensions = extensions
    
    def find_openmp_test_files(self) -> List[Path]:
        """Find all OpenMP test files in the LLVM test directory"""
        if not self.base_dir.exists():
            logger.error(f"Base directory does not exist: {self.base_dir}")
            return []
        
        found_files = set()
        
        # Search using glob patterns
        for pattern in self.patterns:
            try:
                matches = list(self.base_dir.glob(pattern))
                found_files.update(matches)
                logger.debug(f"Pattern '{pattern}' found {len(matches)} files")
            except Exception as e:
                logger.warning(f"Error with pattern '{pattern}': {e}")
        
        # Additional search by walking directory tree
        found_files.update(self._walk_and_filter())
        
        # Filter by extension and validate
        valid_files = []
        for file_path in found_files:
            if (file_path.is_file() and 
                file_path.suffix in self.extensions and
                self._is_openmp_test_file(file_path)):
                valid_files.append(file_path)
        
        logger.info(f"Found {len(valid_files)} OpenMP test files")
        return sorted(valid_files)
    
    def _walk_and_filter(self) -> Set[Path]:
        """Walk directory tree and find OpenMP-related files"""
        found_files = set()
        
        try:
            for file_path in self.base_dir.rglob("*"):
                if (file_path.is_file() and 
                    file_path.suffix in self.extensions and
                    self._matches_openmp_pattern(file_path.name)):
                    found_files.add(file_path)
        except Exception as e:
            logger.error(f"Error walking directory tree: {e}")
        
        return found_files
    
    def _matches_openmp_pattern(self, filename: str) -> bool:
        """Check if filename matches OpenMP patterns"""
        filename_lower = filename.lower()
        openmp_keywords = [
            'openmp', 'omp', 'fopenmp', 'parallel', 'pragma_omp'
        ]
        
        return any(keyword in filename_lower for keyword in openmp_keywords)
    
    def _is_openmp_test_file(self, file_path: Path) -> bool:
        """Verify if file is actually an OpenMP test file"""
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            content_lower = content.lower()
            
            # Check for OpenMP indicators
            openmp_indicators = [
                '#pragma omp',
                '-fopenmp',
                'openmp',
                '__kmpc_',
                'omp_'
            ]
            
            return any(indicator in content_lower for indicator in openmp_indicators)
            
        except Exception as e:
            logger.debug(f"Error checking file {file_path}: {e}")
            return False
