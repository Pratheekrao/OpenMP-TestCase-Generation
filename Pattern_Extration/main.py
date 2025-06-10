#!/usr/bin/env python3

import sys
import logging
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from config import settings
from src.core.analyzer import OpenMPPatternAnalyzer

def setup_logging():
    """Setup logging configuration"""
    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL),
        format=settings.LOG_FORMAT,
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('openmp_analyzer.log')
        ]
    )

def validate_environment():
    """Validate that all required components are available"""
    logger = logging.getLogger(__name__)
    
    # Check LLVM test directory
    if not Path(settings.LLVM_TEST_DIR).exists():
        logger.error(f"LLVM test directory not found: {settings.LLVM_TEST_DIR}")
        logger.error("Please set LLVM_TEST_DIR in config/settings.py")
        logger.error("You can clone LLVM with: git clone https://github.com/llvm/llvm-project.git")
        return False
    
    logger.info(f"✓ LLVM test directory found: {settings.LLVM_TEST_DIR}")
    
    # Test Clang bindings with multiple fallback strategies
    try:
        import clang.cindex
        logger.info("Clang module imported successfully")
        
        # Strategy 1: Try with bundled libclang (from libclang PyPI package)
        try:
            index = clang.cindex.Index.create()
            logger.info("✓ Clang bindings working with bundled libclang library")
            return True
        except Exception as e1:
            logger.debug(f"Bundled libclang failed: {e1}")
        
        # Strategy 2: Try with system library path if configured
        if hasattr(settings, 'CLANG_LIBRARY_PATH') and settings.CLANG_LIBRARY_PATH:
            try:
                if Path(settings.CLANG_LIBRARY_PATH).exists():
                    clang.cindex.Config.set_library_path(settings.CLANG_LIBRARY_PATH)
                    index = clang.cindex.Index.create()
                    logger.info(f"✓ Clang bindings working with system library: {settings.CLANG_LIBRARY_PATH}")
                    return True
                else:
                    logger.warning(f"Configured CLANG_LIBRARY_PATH does not exist: {settings.CLANG_LIBRARY_PATH}")
            except Exception as e2:
                logger.debug(f"System libclang failed: {e2}")
        
        # Strategy 3: Try common system paths
        common_paths = [
            "/usr/lib/llvm-17/lib",
            "/usr/lib/llvm-16/lib", 
            "/usr/lib/llvm-15/lib",
            "/usr/lib/llvm-14/lib",
            "/usr/lib/x86_64-linux-gnu",
            "/opt/homebrew/opt/llvm/lib",  # macOS Apple Silicon
            "/usr/local/opt/llvm/lib",     # macOS Intel
            "/usr/local/lib"
        ]
        
        for path in common_paths:
            if Path(path).exists():
                try:
                    clang.cindex.Config.set_library_path(path)
                    index = clang.cindex.Index.create()
                    logger.info(f"✓ Clang bindings working with discovered library: {path}")
                    return True
                except Exception as e3:
                    logger.debug(f"Path {path} failed: {e3}")
                    continue
        
        # If all strategies failed
        logger.error("✗ All Clang library loading strategies failed")
        logger.error("Solutions:")
        logger.error("  1. Install bundled libclang: pip install libclang")
        logger.error("  2. Install system libclang: sudo apt install libclang-dev")
        logger.error("  3. Set correct CLANG_LIBRARY_PATH in config/settings.py")
        return False
        
    except ImportError as e:
        logger.error(f"✗ Failed to import clang module: {e}")
        logger.error("Install with: pip install libclang")
        return False
    except Exception as e:
        logger.error(f"✗ Unexpected Clang bindings error: {e}")
        return False

def print_system_info():
    """Print system information for debugging"""
    logger = logging.getLogger(__name__)
    
    logger.info("System Information:")
    logger.info(f"  Python version: {sys.version}")
    logger.info(f"  Platform: {sys.platform}")
    
    try:
        import clang.cindex
        logger.info(f"  Clang module location: {clang.cindex.__file__}")
        
        # Try to get libclang version if possible
        try:
            index = clang.cindex.Index.create()
            logger.info("  Clang index created successfully")
        except Exception as e:
            logger.info(f"  Clang index creation failed: {e}")
            
    except ImportError:
        logger.info("  Clang module not available")

def main():
    """Main entry point"""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("OpenMP Pattern Extractor Starting...")
    logger.info("=" * 50)
    
    # Print system information for debugging
    print_system_info()
    
    # Validate environment
    if not validate_environment():
        logger.error("Environment validation failed")
        logger.error("\nTroubleshooting steps:")
        logger.error("1. Install libclang: pip install libclang")
        logger.error("2. Verify LLVM test directory exists")
        logger.error("3. Check config/settings.py configuration")
        sys.exit(1)
    
    try:
        # Initialize analyzer
        logger.info("Initializing OpenMP Pattern Analyzer...")
        analyzer = OpenMPPatternAnalyzer(settings)
        
        # Run analysis
        logger.info("Starting test file analysis...")
        success = analyzer.analyze_all_tests()
        
        if success:
            # Print statistics
            logger.info("\n" + "=" * 50)
            logger.info("ANALYSIS COMPLETE")
            logger.info("=" * 50)
            
            stats = analyzer.get_statistics()
            logger.info("Analysis Statistics:")
            logger.info(f"  Total patterns extracted: {stats.get('total_patterns', 0)}")
            
            if stats.get('by_stage'):
                logger.info("  Patterns by compiler stage:")
                for stage, count in stats['by_stage'].items():
                    logger.info(f"    {stage}: {count}")
            
            if stats.get('by_category'):
                logger.info("  Patterns by test category:")
                for category, count in stats['by_category'].items():
                    logger.info(f"    {category}: {count}")
            
            if stats.get('top_directives'):
                logger.info("  Most common OpenMP directives:")
                for directive, count in list(stats['top_directives'].items())[:5]:
                    logger.info(f"    {directive}: {count}")
            
            # Export patterns
            logger.info(f"\nExporting patterns to {settings.EXPORT_JSON_PATH}...")
            if analyzer.export_patterns(settings.EXPORT_JSON_PATH):
                logger.info(f"✓ Patterns exported successfully")
                logger.info(f"  Database: {settings.DATABASE_PATH}")
                logger.info(f"  JSON export: {settings.EXPORT_JSON_PATH}")
            else:
                logger.warning("Failed to export patterns to JSON")
            
            logger.info("\n✓ OpenMP pattern extraction completed successfully!")
            
        else:
            logger.error("✗ Analysis failed - no patterns were extracted")
            logger.error("Check the logs above for specific error details")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("\nAnalysis interrupted by user (Ctrl+C)")
        logger.info("Partial results may be available in the database")
        sys.exit(0)
        
    except Exception as e:
        logger.error(f"\nUnexpected error during analysis: {e}", exc_info=True)
        logger.error("This may indicate a bug in the analyzer")
        logger.error("Please check the full error trace above")
        sys.exit(1)

def test_clang_functionality():
    """Test basic Clang functionality - can be run separately"""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("Testing Clang functionality...")
    
    try:
        import clang.cindex
        
        # Create a simple test file
        test_code = '''
        #pragma omp parallel
        {
            int x = 42;
        }
        '''
        
        # Try to parse it
        index = clang.cindex.Index.create()
        tu = index.parse('test.c', unsaved_files=[('test.c', test_code)], 
                        args=['-fopenmp'])
        
        if tu:
            logger.info("✓ Successfully parsed test OpenMP code")
            
            # Try to traverse AST
            def traverse(node, depth=0):
                if depth < 5:  # Limit depth
                    logger.debug(f"{'  ' * depth}Node: {node.kind} - {node.spelling}")
                    for child in node.get_children():
                        traverse(child, depth + 1)
            
            traverse(tu.cursor)
            logger.info("✓ Successfully traversed AST")
            return True
        else:
            logger.error("✗ Failed to parse test code")
            return False
            
    except Exception as e:
        logger.error(f"✗ Clang functionality test failed: {e}")
        return False

if __name__ == "__main__":
    # Allow running clang test separately
    if len(sys.argv) > 1 and sys.argv[1] == "--test-clang":
        test_clang_functionality()
    else:
        main()
