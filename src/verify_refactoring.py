"""
Verification Script for API Refactoring
Run this script to verify that all refactored modules are importable and backward compatibility is maintained.
"""
import logging
import os
import sys

# Add project root to sys.path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def verify_module(name, legacy_path, new_path):
    logger.info("Verifying %s...", name)
    try:
        # 1. Verify New Module Import
        logger.info("  Importing new module: %s", new_path)
        __import__(new_path)

        # 2. Verify Legacy Proxy Import
        logger.info("  Importing legacy proxy: %s", legacy_path)
        legacy = __import__(legacy_path, fromlist=["*"])

        # 3. Verify Exports
        if hasattr(legacy, "router"):
            logger.info("  ✅ Router exported correctly")
        else:
            logger.error("  ❌ Router NOT exported from legacy proxy")
            return False

        logger.info("✅ %s verification passed", name)
        return True
    except ImportError as e:
        logger.error("❌ ImportError in %s: {e}", name)
        return False
    except Exception as e:
        logger.error("❌ Unexpected error in %s: {e}", name)
        return False


def main():
    logger.info("Starting Refactoring Verification")

    modules_to_verify = [
        ("BA Sessions", "src.api.ba_sessions", "src.modules.ba_sessions"),
        ("Copilot API", "src.api.copilot_api_perfect", "src.modules.copilot"),
        ("Code Analyzers", "src.api.code_analyzers", "src.modules.code_analyzers"),
        ("Code Approval", "src.api.code_approval", "src.modules.code_approval"),
        ("Assistants", "src.api.assistants", "src.modules.assistants"),
        ("Metrics", "src.api.metrics", "src.modules.metrics"),
    ]

    success_count = 0
    for name, legacy, new in modules_to_verify:
        if verify_module(name, legacy, new):
            success_count += 1

    logger.info("-" * 30)
    if success_count == len(modules_to_verify):
        logger.info("✅ ALL %s MODULES VERIFIED SUCCESSFULLY", success_count)
        sys.exit(0)
    else:
        logger.error(
            f"❌ FAILED: Only {success_count}/{len(modules_to_verify)} modules verified")
        sys.exit(1)


if __name__ == "__main__":
    main()
