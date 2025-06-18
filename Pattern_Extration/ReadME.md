# OpenMP Pattern Extraction Tool

An automated Python-based tool designed to extract meaningful patterns from existing OpenMP test cases. This tool analyzes OpenMP test files, extracts directive patterns, error patterns, and test metadata, and stores them in a structured SQLite database for efficient retrieval and use in test generation.

## Features

- **AST-Based Analysis**: Utilizes Clang's Python bindings or regex-based parsing to analyze OpenMP directives and clauses.
- **Pattern Classification**: Categorizes tests by compiler stage (Parse, Sema, CodeGen) and test category (parallel, worksharing, target, etc.).
- **Error Pattern Detection**: Identifies expected errors and negative test cases.
- **Complexity Scoring**: Assigns complexity scores based on directive count, clause combinations, and error patterns.
- **Database Storage**: Stores extracted patterns in a normalized SQLite database with optimized indexing.
- **Run Command Extraction**: Parses RUN commands and CHECK patterns from test files.
- **Scalable Processing**: Supports batch processing of large test suites.

## Prerequisites

- Python 3.8 or higher  
- SQLite3  
- Clang Python bindings (optional, if using AST analysis)  
- Required Python packages:
  - `clang` (for AST parsing)
  - `sqlite3` (standard library)
  - `json`
  - `re`
  - `os`
  - `argparse`

## Installation

1. Clone the repository:

```bash
git clone <repository-url>
cd openmp-pattern-extractor-python
```

2. Install required Python packages:

```bash
pip install clang
```

3. Ensure SQLite3 is installed on your system.

## Usage

Run the pattern extraction script with the directory containing OpenMP test files:

```bash
python extract_patterns.py --input-dir /path/to/openmp/tests --output-db openmp_patterns.db
```

## Command Line Arguments

- `--input-dir`: Path to the directory containing OpenMP test files.  
- `--output-db`: Path to the SQLite database file to store extracted patterns.  
- `--verbose`: Enable verbose logging.

## Output

- A SQLite database containing extracted patterns, directives, error patterns, and test metadata.

## Example

```bash
python extract_patterns.py --input-dir ./clang/test/OpenMP --output-db openmp_patterns.db --verbose
```
