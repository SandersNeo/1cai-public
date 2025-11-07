#!/bin/bash
################################################################################
# EDT Configuration Analysis - Full Pipeline Orchestrator
# 
# Purpose: Automate and parallelize 6-step EDT analysis pipeline
# Version: 1.0.0
# Date: 2025-11-06
#
# Pipeline:
# 1. Parse EDT configuration (sequential, 10-15 min)
# 2-5. Run 4 parallel analyses (parallel, 8-12 min total)
#    - Architecture analysis
#    - ML dataset creation
#    - Dependencies analysis
#    - Best practices extraction
# 6. Generate documentation (sequential, 1-2 min)
#
# Time savings: 30-47 min → 15-20 min (-35-50%)
#
# Usage:
#   ./scripts/orchestrate_edt_analysis.sh
#   ./scripts/orchestrate_edt_analysis.sh --config ERPCPM
#   ./scripts/orchestrate_edt_analysis.sh --help
################################################################################

set -e  # Exit on error
set -u  # Exit on undefined variable
set -o pipefail  # Pipe failures are errors

# ============================================================================
# CONFIGURATION
# ============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
LOG_DIR="$PROJECT_ROOT/logs/edt_analysis"
OUTPUT_DIR="$PROJECT_ROOT/output"

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RUN_ID="edt_analysis_$TIMESTAMP"
LOG_FILE="$LOG_DIR/${RUN_ID}.log"

# Default configuration
CONFIG_NAME="${1:-ERPCPM}"
CONFIG_PATH="$PROJECT_ROOT/1c_configurations/$CONFIG_NAME"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ============================================================================
# FUNCTIONS
# ============================================================================

log() {
    local level="$1"
    local message="$2"
    local timestamp=$(date +'%Y-%m-%d %H:%M:%S')
    local color=""
    
    case "$level" in
        "INFO")  color="$BLUE" ;;
        "SUCCESS") color="$GREEN" ;;
        "WARNING") color="$YELLOW" ;;
        "ERROR") color="$RED" ;;
        *) color="$NC" ;;
    esac
    
    echo -e "${color}[$timestamp] [$level] $message${NC}" | tee -a "$LOG_FILE"
}

print_header() {
    local title="$1"
    log "INFO" "========================================="
    log "INFO" "$title"
    log "INFO" "========================================="
}

print_footer() {
    log "INFO" "========================================="
}

check_requirements() {
    log "INFO" "Checking requirements..."
    
    # Check Python
    if ! command -v python &> /dev/null && ! command -v python3 &> /dev/null; then
        log "ERROR" "Python not found. Please install Python 3.11.x"
        exit 1
    fi
    
    PYTHON_CMD=$(command -v python3 || command -v python)
    
    # Check configuration directory
    if [ ! -d "$CONFIG_PATH" ]; then
        log "ERROR" "Configuration not found: $CONFIG_PATH"
        log "INFO" "Available configurations:"
        ls -1 "$PROJECT_ROOT/1c_configurations/" 2>/dev/null || echo "  None"
        exit 1
    fi
    
    # Check required scripts
    local required_scripts=(
        "parsers/edt/edt_parser_with_metadata.py"
        "analysis/analyze_architecture.py"
        "dataset/create_ml_dataset.py"
        "analysis/analyze_dependencies.py"
        "analysis/extract_best_practices.py"
        "analysis/generate_documentation.py"
    )
    
    for script in "${required_scripts[@]}"; do
        if [ ! -f "$SCRIPT_DIR/$script" ]; then
            log "ERROR" "Required script not found: $script"
            exit 1
        fi
    done
    
    log "SUCCESS" "✅ All requirements OK"
}

create_directories() {
    mkdir -p "$LOG_DIR"
    mkdir -p "$OUTPUT_DIR/edt_parser"
    mkdir -p "$OUTPUT_DIR/analysis"
    mkdir -p "$OUTPUT_DIR/dataset"
    mkdir -p "$PROJECT_ROOT/docs/generated"
}

run_step() {
    local step_num="$1"
    local step_name="$2"
    local command="$3"
    local timeout_seconds="${4:-1800}"  # Default 30 min
    
    log "INFO" "Step $step_num: $step_name..."
    local start_time=$(date +%s)
    
    # Run with timeout
    timeout $timeout_seconds bash -c "$command" >> "$LOG_FILE" 2>&1
    local exit_code=$?
    
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    if [ $exit_code -eq 124 ]; then
        log "ERROR" "❌ $step_name TIMEOUT (>${timeout_seconds}s)"
        return 1
    elif [ $exit_code -ne 0 ]; then
        log "ERROR" "❌ $step_name FAILED (exit code: $exit_code, duration: ${duration}s)"
        return 1
    else
        log "SUCCESS" "✅ $step_name complete (${duration}s)"
        return 0
    fi
}

show_usage() {
    cat << EOF
EDT Analysis Pipeline Orchestrator

Usage:
  $0 [OPTIONS] [CONFIG_NAME]

Arguments:
  CONFIG_NAME    Configuration name (default: ERPCPM)
                 Must exist in 1c_configurations/ directory

Options:
  -h, --help     Show this help message
  --dry-run      Show what would be executed without running
  --skip-parse   Skip parsing step (use existing parse results)

Examples:
  $0                    # Analyze ERPCPM (default)
  $0 ERP                # Analyze ERP configuration
  $0 --skip-parse       # Skip parsing, run only analysis

Output:
  Logs: $LOG_DIR/
  Results: $OUTPUT_DIR/

EOF
}

# ============================================================================
# MAIN PIPELINE
# ============================================================================

main() {
    # Parse arguments
    if [[ "${1:-}" == "-h" ]] || [[ "${1:-}" == "--help" ]]; then
        show_usage
        exit 0
    fi
    
    local SKIP_PARSE=false
    if [[ "${1:-}" == "--skip-parse" ]]; then
        SKIP_PARSE=true
        shift
    fi
    
    print_header "EDT ANALYSIS PIPELINE"
    log "INFO" "Run ID: $RUN_ID"
    log "INFO" "Configuration: $CONFIG_NAME"
    log "INFO" "Log file: $LOG_FILE"
    print_footer
    
    # Setup
    create_directories
    check_requirements
    
    # Determine Python command
    PYTHON_CMD=$(command -v python3 || command -v python)
    
    # Global start time
    PIPELINE_START=$(date +%s)
    
    # ========================================================================
    # STEP 1: Parsing (обязательно первым)
    # ========================================================================
    
    if [ "$SKIP_PARSE" = false ]; then
        if ! run_step "1/6" \
            "Parsing EDT configuration" \
            "cd '$PROJECT_ROOT' && $PYTHON_CMD scripts/parsers/edt/edt_parser_with_metadata.py" \
            1200; then
            log "ERROR" "Pipeline aborted at parsing step"
            exit 1
        fi
    else
        log "WARNING" "Skipping parsing step (using existing results)"
    fi
    
    # ========================================================================
    # STEPS 2-5: Parallel Analysis (4 независимых задачи)
    # ========================================================================
    
    print_header "PARALLEL ANALYSIS (4 tasks)"
    
    PARALLEL_START=$(date +%s)
    
    # Запускаем 4 задачи в фоне
    log "INFO" "Launching 4 parallel analyses..."
    
    # Analysis 1: Architecture
    (
        cd "$PROJECT_ROOT"
        $PYTHON_CMD scripts/analysis/analyze_architecture.py > "$LOG_DIR/${RUN_ID}_arch.log" 2>&1
        echo $? > "$LOG_DIR/${RUN_ID}_arch.exit"
    ) &
    PID_ARCH=$!
    
    # Analysis 2: ML Dataset
    (
        cd "$PROJECT_ROOT"
        $PYTHON_CMD scripts/dataset/create_ml_dataset.py > "$LOG_DIR/${RUN_ID}_dataset.log" 2>&1
        echo $? > "$LOG_DIR/${RUN_ID}_dataset.exit"
    ) &
    PID_DATASET=$!
    
    # Analysis 3: Dependencies
    (
        cd "$PROJECT_ROOT"
        $PYTHON_CMD scripts/analysis/analyze_dependencies.py > "$LOG_DIR/${RUN_ID}_deps.log" 2>&1
        echo $? > "$LOG_DIR/${RUN_ID}_deps.exit"
    ) &
    PID_DEPS=$!
    
    # Analysis 4: Best Practices
    (
        cd "$PROJECT_ROOT"
        $PYTHON_CMD scripts/analysis/extract_best_practices.py > "$LOG_DIR/${RUN_ID}_bp.log" 2>&1
        echo $? > "$LOG_DIR/${RUN_ID}_bp.exit"
    ) &
    PID_BP=$!
    
    log "INFO" "  Process IDs: ARCH=$PID_ARCH, DATASET=$PID_DATASET, DEPS=$PID_DEPS, BP=$PID_BP"
    log "INFO" "Waiting for all analyses to complete..."
    
    # Ждём завершения всех задач
    wait $PID_ARCH
    wait $PID_DATASET
    wait $PID_DEPS
    wait $PID_BP
    
    PARALLEL_END=$(date +%s)
    PARALLEL_DURATION=$((PARALLEL_END - PARALLEL_START))
    
    # Проверяем exit codes
    FAILED_COUNT=0
    
    EXIT_ARCH=$(cat "$LOG_DIR/${RUN_ID}_arch.exit" 2>/dev/null || echo "1")
    if [ "$EXIT_ARCH" -eq 0 ]; then
        log "SUCCESS" "  ✅ Architecture analysis complete"
    else
        log "ERROR" "  ❌ Architecture analysis FAILED"
        FAILED_COUNT=$((FAILED_COUNT + 1))
    fi
    
    EXIT_DATASET=$(cat "$LOG_DIR/${RUN_ID}_dataset.exit" 2>/dev/null || echo "1")
    if [ "$EXIT_DATASET" -eq 0 ]; then
        log "SUCCESS" "  ✅ ML Dataset creation complete"
    else
        log "ERROR" "  ❌ ML Dataset creation FAILED"
        FAILED_COUNT=$((FAILED_COUNT + 1))
    fi
    
    EXIT_DEPS=$(cat "$LOG_DIR/${RUN_ID}_deps.exit" 2>/dev/null || echo "1")
    if [ "$EXIT_DEPS" -eq 0 ]; then
        log "SUCCESS" "  ✅ Dependencies analysis complete"
    else
        log "ERROR" "  ❌ Dependencies analysis FAILED"
        FAILED_COUNT=$((FAILED_COUNT + 1))
    fi
    
    EXIT_BP=$(cat "$LOG_DIR/${RUN_ID}_bp.exit" 2>/dev/null || echo "1")
    if [ "$EXIT_BP" -eq 0 ]; then
        log "SUCCESS" "  ✅ Best practices extraction complete"
    else
        log "ERROR" "  ❌ Best practices extraction FAILED"
        FAILED_COUNT=$((FAILED_COUNT + 1))
    fi
    
    log "INFO" "Parallel analysis completed in ${PARALLEL_DURATION}s"
    
    if [ $FAILED_COUNT -gt 0 ]; then
        log "ERROR" "Pipeline failed: $FAILED_COUNT tasks failed"
        log "INFO" "Check individual logs in: $LOG_DIR/"
        exit 1
    fi
    
    print_footer
    
    # ========================================================================
    # STEP 6: Documentation (после всех анализов)
    # ========================================================================
    
    if ! run_step "6/6" \
        "Generating documentation" \
        "cd '$PROJECT_ROOT' && $PYTHON_CMD scripts/analysis/generate_documentation.py" \
        300; then
        log "ERROR" "Documentation generation failed (non-critical)"
        # Не останавливаем pipeline, документация - не критична
    fi
    
    # ========================================================================
    # SUMMARY
    # ========================================================================
    
    PIPELINE_END=$(date +%s)
    TOTAL_DURATION=$((PIPELINE_END - PIPELINE_START))
    
    print_header "PIPELINE COMPLETE"
    log "SUCCESS" "✅✅✅ ALL STEPS COMPLETED ✅✅✅"
    print_footer
    
    log "INFO" "Summary:"
    log "INFO" "  Total time: ${TOTAL_DURATION}s ($(echo "scale=1; $TOTAL_DURATION/60" | bc) min)"
    log "INFO" ""
    log "INFO" "Results:"
    log "INFO" "  📊 Parse results:     $OUTPUT_DIR/edt_parser/"
    log "INFO" "  🏗️  Architecture:      $OUTPUT_DIR/analysis/architecture_analysis.json"
    log "INFO" "  🔗 Dependencies:      $OUTPUT_DIR/analysis/dependency_graph.json"
    log "INFO" "  💾 ML Dataset:        $OUTPUT_DIR/dataset/ml_training_dataset.json"
    log "INFO" "  📖 Best practices:    $OUTPUT_DIR/analysis/best_practices.json"
    log "INFO" "  📝 Documentation:     docs/generated/"
    log "INFO" ""
    log "INFO" "Logs:"
    log "INFO" "  Main log:             $LOG_FILE"
    log "INFO" "  Architecture:         $LOG_DIR/${RUN_ID}_arch.log"
    log "INFO" "  ML Dataset:           $LOG_DIR/${RUN_ID}_dataset.log"
    log "INFO" "  Dependencies:         $LOG_DIR/${RUN_ID}_deps.log"
    log "INFO" "  Best practices:       $LOG_DIR/${RUN_ID}_bp.log"
    
    print_footer
    
    # Cleanup temporary exit code files
    rm -f "$LOG_DIR/${RUN_ID}"_*.exit
}

# ============================================================================
# ENTRY POINT
# ============================================================================

# Show help
if [[ "${1:-}" == "-h" ]] || [[ "${1:-}" == "--help" ]]; then
    show_usage
    exit 0
fi

# Run pipeline
main "$@"


