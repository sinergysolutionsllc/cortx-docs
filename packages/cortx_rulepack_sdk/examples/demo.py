"""
RulePack SDK Demo

This script demonstrates how to use the CORTX RulePack SDK.
"""

import asyncio

from cortx_rulepack_sdk.contracts import ValidationMode
from cortx_rulepack_sdk.testing import MockRulePackData, run_rulepack_tests
from examples.example_rulepack import ExampleRulePack


async def demo_basic_usage():
    """Demonstrate basic RulePack usage"""
    print("🚀 CORTX RulePack SDK Demo")
    print("=" * 50)

    # Create and initialize RulePack
    config = {
        "rules_path": None,  # Use default rules
        "debug": True,
    }

    rulepack = ExampleRulePack(config)

    async with rulepack.lifespan():
        print(f"✅ Initialized {rulepack.name} v{rulepack.version}")

        # Get RulePack information
        info = await rulepack.get_info()
        print(f"📋 Domain: {info.domain}")
        print(f"📋 Rules: {info.rule_count}")
        print(f"📋 Categories: {', '.join(info.categories)}")
        print(
            f"📋 Modes: {', '.join([m.value if hasattr(m, 'value') else str(m) for m in info.supported_modes])}"
        )
        print()

        # Demo 1: Valid record
        print("Demo 1: Valid Record")
        print("-" * 20)

        valid_record = {
            "account": "123456",
            "amount": 1500.50,
            "date": "2024-01-15",
            "description": "Test transaction",
        }

        request = MockRulePackData.validation_request(
            domain="example", input_data=valid_record, mode=ValidationMode.STATIC
        )

        response = await rulepack.validate(request)

        print(f"✅ Status: {'SUCCESS' if response.success else 'FAILED'}")
        print(f"📊 Records processed: {response.summary.records_processed}")
        print(f"❌ Failures: {response.summary.total_failures}")
        print(f"⏱️  Processing time: {response.summary.processing_time_ms}ms")
        print()

        # Demo 2: Invalid record
        print("Demo 2: Invalid Record")
        print("-" * 20)

        invalid_record = {
            "account": "12345",  # Wrong format (5 digits instead of 6)
            "amount": "invalid",  # Not a number
            "date": "2024-13-45",  # Invalid date
            # Missing required fields
        }

        request = MockRulePackData.validation_request(
            domain="example", input_data=invalid_record, mode=ValidationMode.STATIC
        )

        response = await rulepack.validate(request)

        print(f"✅ Status: {'SUCCESS' if response.success else 'FAILED'}")
        print(f"📊 Records processed: {response.summary.records_processed}")
        print(f"❌ Failures: {response.summary.total_failures}")
        print(f"⏱️  Processing time: {response.summary.processing_time_ms}ms")
        print()

        # Show failure details
        print("Failure Details:")
        for i, failure in enumerate(response.failures[:5], 1):  # Show first 5
            print(f"  {i}. {failure.rule_name} ({failure.severity.upper()})")
            print(f"     Field: {failure.field or 'N/A'}")
            print(f"     Issue: {failure.failure_description}")

            # Get explanation
            from cortx_rulepack_sdk.contracts import ExplanationRequest

            explanation_request = ExplanationRequest(failure=failure)
            explanation = await rulepack.explain(explanation_request)

            print(f"     💡 Explanation: {explanation.explanation}")
            print(f"     🔧 Recommendation: {explanation.recommendation}")
            print()

        # Demo 3: Multiple records
        print("Demo 3: Batch Processing")
        print("-" * 25)

        batch_records = [
            {"account": "111111", "amount": 100, "date": "2024-01-01"},
            {"account": "222222", "amount": -50, "date": "2024-01-02"},
            {"account": "invalid", "amount": 200, "date": "2024-01-03"},  # Invalid account
            {
                "account": "333333",
                "amount": 999999999,
                "date": "2024-01-04",
            },  # Large amount warning
        ]

        request = MockRulePackData.validation_request(
            domain="example", input_data=batch_records, mode=ValidationMode.STATIC
        )

        response = await rulepack.validate(request)

        print(f"✅ Status: {'SUCCESS' if response.success else 'FAILED'}")
        print(f"📊 Records processed: {response.summary.records_processed}")
        print(f"❌ Total failures: {response.summary.total_failures}")
        print(f"🚨 Errors: {response.summary.error_count}")
        print(f"⚠️  Warnings: {response.summary.warning_count}")
        print(f"⏱️  Processing time: {response.summary.processing_time_ms}ms")
        print()


async def demo_sdk_testing():
    """Demonstrate SDK testing utilities"""
    print("🧪 RulePack Testing Demo")
    print("=" * 30)

    # Run contract tests
    results = await run_rulepack_tests(ExampleRulePack, verbose=True)

    print("\n📊 Test Summary:")
    summary = results["summary"]
    print(f"   Total: {summary['total']}")
    print(f"   Passed: {summary['passed']}")
    print(f"   Failed: {summary['failed']}")
    print(f"   Success Rate: {summary['success_rate']:.1%}")

    if summary["failed"] > 0:
        print("\n❌ Failed Tests:")
        for result in results["results"]:
            if result["status"] == "FAILED":
                print(f"   • {result['test']}: {result['message']}")


async def main():
    """Run all demos"""
    try:
        await demo_basic_usage()
        await demo_sdk_testing()

        print("🎉 Demo completed successfully!")

    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
