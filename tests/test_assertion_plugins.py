"""
Test assertion plugin functionality.
"""

from that import test, suite, that


with suite("Assertion Plugin System"):
    
    @test("assertion plugins are loaded")
    def test_assertion_plugins_loaded():
        """Test that assertion plugins are loaded and available."""
        from that.plugins.registry import plugin_registry
        
        # Should have assertion methods from plugins
        assertion_methods = plugin_registry.get_assertion_methods()
        that(len(assertion_methods)).is_greater_than(0)

    @test("custom assertion methods are available")
    def test_custom_assertion_methods():
        """Test that custom assertion methods are dynamically added."""
        # These methods should be available from the example assertion plugin
        test_assertion = that("test@example.com")
        
        # Check if the method exists (it should be added dynamically)
        that(hasattr(test_assertion, 'is_email')).is_true()


with suite("Example Assertion Plugin"):
    
    @test("is_email validates email addresses")
    def test_is_email():
        """Test email validation assertion."""
        that("user@example.com").is_email()
        that("test.email+tag@domain.co.uk").is_email()
        
        # Test failure cases
        def invalid_email():
            that("not-an-email").is_email()
        that(invalid_email).raises(Exception)

    @test("is_url validates URLs")
    def test_is_url():
        """Test URL validation assertion."""
        that("https://example.com").is_url()
        that("http://test.org/path?query=value").is_url()
        
        # Test failure cases
        def invalid_url():
            that("not-a-url").is_url()
        that(invalid_url).raises(Exception)

    @test("is_positive validates positive numbers")
    def test_is_positive():
        """Test positive number assertion."""
        that(5).is_positive()
        that(3.14).is_positive()
        
        # Test failure cases
        def negative_number():
            that(-1).is_positive()
        that(negative_number).raises(Exception)
        
        def zero():
            that(0).is_positive()
        that(zero).raises(Exception)

    @test("is_even validates even numbers")
    def test_is_even():
        """Test even number assertion."""
        that(2).is_even()
        that(0).is_even()
        that(-4).is_even()
        
        # Test failure cases
        def odd_number():
            that(3).is_even()
        that(odd_number).raises(Exception)

    @test("is_odd validates odd numbers")
    def test_is_odd():
        """Test odd number assertion."""
        that(1).is_odd()
        that(3).is_odd()
        that(-5).is_odd()
        
        # Test failure cases
        def even_number():
            that(4).is_odd()
        that(even_number).raises(Exception)

    @test("has_length_between validates length ranges")
    def test_has_length_between():
        """Test length range assertion."""
        that("hello").has_length_between(3, 10)
        that([1, 2, 3]).has_length_between(2, 5)
        that({"a": 1, "b": 2}).has_length_between(1, 3)
        
        # Test failure cases
        def too_short():
            that("hi").has_length_between(5, 10)
        that(too_short).raises(Exception)
        
        def too_long():
            that("very long string").has_length_between(1, 5)
        that(too_long).raises(Exception)
