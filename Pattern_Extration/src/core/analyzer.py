import logging
from pathlib import Path
from typing import List, Optional

from ..database.storage import PatternDatabase
from ..database.models import TestPattern
from ..utils.file_finder import OpenMPFileFinder
from .ast_extractor import ASTExtractor
from .file_processor import FileProcessor

logger = logging.getLogger(__name__)

class OpenMPPatternAnalyzer:
    def __init__(self, config):
        self.config = config
        self.database = PatternDatabase(config.DATABASE_PATH)
        self.ast_extractor = ASTExtractor(
            '', 
            config.CLANG_ARGS
        )
        self.file_processor = FileProcessor(self.ast_extractor)
        self.file_finder = OpenMPFileFinder(
            config.LLVM_TEST_DIR,
            config.OPENMP_TEST_PATTERNS,
            config.SUPPORTED_EXTENSIONS
        )
    
    def analyze_all_tests(self) -> bool:
        """Analyze all OpenMP test files and store patterns"""
        logger.info("Starting OpenMP test analysis...")
        
        # Find all test files
        test_files = self.file_finder.find_openmp_test_files()
        if not test_files:
            logger.error("No OpenMP test files found")
            return False
        
        logger.info(f"Found {len(test_files)} test files to analyze")
        
        # Process each file
        successful_count = 0
        failed_count = 0
        
        for i, test_file in enumerate(test_files, 1):
            logger.info(f"Processing [{i}/{len(test_files)}]: {test_file.name}")
            
            try:
                pattern = self.file_processor.process_test_file(test_file)
                if pattern:
                    if self.database.store_pattern(pattern):
                        successful_count += 1
                    else:
                        failed_count += 1
                        logger.warning(f"Failed to store pattern for {test_file}")
                else:
                    failed_count += 1
                    logger.warning(f"Failed to extract pattern from {test_file}")
                    
            except Exception as e:
                failed_count += 1
                logger.error(f"Error processing {test_file}: {e}")
            
            # Progress update
            if i % 50 == 0:
                logger.info(f"Progress: {i}/{len(test_files)} files processed")
        
        logger.info(f"Analysis complete: {successful_count} successful, {failed_count} failed")
        return successful_count > 0
    
    def get_statistics(self) -> dict:
        """Get analysis statistics"""
        return self.database.get_statistics()
    
    def export_patterns(self, output_path: str) -> bool:
        """Export extracted patterns to JSON"""
        return self.database.export_to_json(output_path)
