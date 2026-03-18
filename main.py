"""
Main entry point for RootCause AI
"""
import asyncio
import logging
import sys
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

from config.schema import ExecutionState
from graph.debug_workflow import DebugWorkflow
from memory.memory_manager import MemoryManager


async def main():
    """Main entry point for CLI execution"""
    logger.info("🔍 RootCause AI - Multi-Agent Debugging System")
    logger.info("=" * 60)

    # Example usage
    print("\n📋 EXAMPLE USAGE:")
    print("=" * 60)

    # Get user input
    print("\n💬 Enter your issue description (or press Enter for example):")
    user_query = input().strip()

    if not user_query:
        user_query = "The application crashes with a RecursionError when processing large nested JSON objects"

    print("\n📁 Enter codebase path (or press Enter for ./sample_code):")
    codebase_path = input().strip() or "./sample_code"

    # Create execution state
    execution_state = ExecutionState(
        user_query=user_query,
        codebase_path=codebase_path,
    )

    # Initialize system components
    logger.info(f"🚀 Starting debugging workflow for: {user_query[:50]}...")
    logger.info(f"📂 Analyzing codebase: {codebase_path}")

    workflow = DebugWorkflow()
    memory_manager = MemoryManager()

    # Execute workflow
    try:
        final_state = await workflow.execute(execution_state)

        # Display results
        print("\n" + "=" * 60)
        print("✅ DEBUGGING ANALYSIS COMPLETE")
        print("=" * 60)

        print(f"\n🎯 Root Cause: {final_state.root_cause}")
        print(f"📈 Confidence: {final_state.root_cause_confidence:.1%}")

        if final_state.affected_files:
            print(f"\n📁 Affected Files:")
            for file in final_state.affected_files:
                print(f"  - {file}")

        if final_state.possible_fixes:
            print(f"\n🔧 Suggested Fixes:")
            for i, fix in enumerate(final_state.possible_fixes, 1):
                print(f"  {i}. {fix}")

        if final_state.alternative_hypotheses:
            print(f"\n🔄 Alternative Hypotheses:")
            for hyp in final_state.alternative_hypotheses:
                print(f"  - {hyp}")

        # Show agent logs
        print(f"\n📜 Agent Activity Log:")
        for log in final_state.agent_logs:
            print(f"  {log}")

        # Save results
        print("\n💾 Saving results to memory...")
        memory_manager.record_bug_finding({
            "issue": user_query,
            "root_cause": final_state.root_cause,
            "affected_files": final_state.affected_files,
            "confidence": final_state.root_cause_confidence,
        })

        print("✅ Results saved successfully")

        # Print memory stats
        print("\n📊 Memory Statistics:")
        stats = memory_manager.get_memory_stats()
        print(f"  Session Events: {stats['short_term']['entries']}")
        print(f"  Total Patterns: {stats['long_term']['total_bug_patterns']}")
        print(f"  Total Solutions: {stats['long_term']['total_solutions']}")

    except Exception as e:
        logger.error(f"❌ Error during workflow execution: {e}", exc_info=True)
        sys.exit(1)

    print("\n" + "=" * 60)
    print("Thank you for using RootCause AI! 🔍")
    print("=" * 60)


if __name__ == "__main__":
    # Run workflow
    asyncio.run(main())
