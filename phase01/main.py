"""
Phase 01 Entry Point for XENON.
"""

import sys
import json
import argparse
from phase01.core.logger import logger
from phase01.core.target_manager import TargetManager
from phase01.core.scope_manager import ScopeManager
from phase01.core.exceptions import XenonException
from phase01.config.settings import settings
from phase01.config.defaults import DEFAULT_TARGET_URL, DEFAULT_SCOPE_CONFIG


def main():
    """Main execution entry point."""
    logger.info("XENON Phase 01 initialization started.")

    try:
        # Parse command line arguments
        parser = argparse.ArgumentParser(description='XENON Phase 01 initialization')
        parser.add_argument('--target', type=str, help='Target URL')
        parser.add_argument('--scope', type=str, help='Scope configuration as JSON string')
        args = parser.parse_args()

        # Use provided target or default
        target_url = args.target if args.target else DEFAULT_TARGET_URL

        # Use provided scope or default
        if args.scope:
            try:
                scope_config = json.loads(args.scope)
            except json.JSONDecodeError as e:
                raise XenonException(f"Invalid JSON scope provided: {e}")
        else:
            scope_config = DEFAULT_SCOPE_CONFIG

        # Initialize Managers
        target_mgr = TargetManager()
        scope_mgr = ScopeManager()

        # Load target
        target_mgr.set_target(target_url)

        # Load and set scope
        scope_mgr.load_scope(scope_config)

        # Basic Status
        logger.info("--- Phase 01 Initialization Status ---")
        logger.info(f"Target: {target_mgr.get_target_url()}")
        logger.info(f"Target Status: {target_mgr.get_target().status if target_mgr.get_target() else 'UNKNOWN'}")
        logger.info("Scope Enforcement: ENABLED")
        logger.info("----------------------------------------")

        logger.info("XENON Phase 01 initialized successfully.")

    except XenonException as e:
        logger.error(f"XENON error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during initialization: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()