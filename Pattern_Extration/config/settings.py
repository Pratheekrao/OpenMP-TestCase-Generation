import os
from pathlib import Path

# LLVM Configuration
LLVM_TEST_DIR = os.getenv("LLVM_TEST_DIR", "/home/pratheek/CD_LAB/llvm-project/clang/test/OpenMP")

# Clang Library Path (optional - will auto-detect if not set)
# Leave empty to use bundled libclang from PyPI package
CLANG_LIBRARY_PATH = os.getenv("CLANG_LIBRARY_PATH", "")

# Database Configuration
DATABASE_PATH = "openmp_patterns.db"
EXPORT_JSON_PATH = "extracted_patterns.json"

# Analysis Configuration
SUPPORTED_EXTENSIONS = ['.c', '.cpp', '.cc', '.cxx']
OPENMP_TEST_PATTERNS = [
    "**/openmp*.c",
    "**/openmp*.cpp",
    "**/OpenMP/**/*.c", 
    "**/OpenMP/**/*.cpp",
    "**/fopenmp*.c",
    "**/fopenmp*.cpp"
]

# Clang Configuration
CLANG_ARGS = [
    '-fopenmp',
    '-std=c++17',
    '-I/usr/include',
    '-I/usr/local/include'
]

# Logging Configuration
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
