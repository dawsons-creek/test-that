"""Test the improved async runner implementation."""

import asyncio
from test_that import test, that, suite
from test_that.async_runner import AsyncTestRunner


with suite("Async Runner Tests"):
    
    @test("async tests run successfully")
    async def test_async_execution():
        """Test that async tests execute properly."""
        await asyncio.sleep(0.01)  # Small delay to ensure async behavior
        that(1 + 1).equals(2)
    
    @test("sync and async tests can be mixed")
    def test_sync_execution():
        """Test that sync tests still work alongside async tests."""
        that("hello").equals("hello")
    
    @test("async runner handles multiple concurrent tests")
    async def test_concurrent_execution():
        """Test concurrent async test execution."""
        start = asyncio.get_event_loop().time()
        
        # Simulate some async work
        await asyncio.gather(
            asyncio.sleep(0.01),
            asyncio.sleep(0.01),
            asyncio.sleep(0.01)
        )
        
        # Should complete in ~0.01s due to concurrency, not 0.03s
        elapsed = asyncio.get_event_loop().time() - start
        that(elapsed).is_less_than(0.02)
    
    @test("async runner provides clean error messages")
    async def test_async_error_handling():
        """Test that async test failures are handled properly."""
        await asyncio.sleep(0.001)
        # This will fail and should produce a clean error
        that(42).equals(43)