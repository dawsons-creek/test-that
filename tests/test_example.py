"""
Example tests for the That testing library.

Demonstrates the basic usage and features.
"""

from test_that import suite, test, that


# Simple standalone tests
@test("basic math works")
def test_math():
    that(2 + 2).equals(4)


@test("string operations")
def test_strings():
    that("hello".upper()).equals("HELLO")
    that("hello world").contains("world")
    that("hello").starts_with("he")
    that("world").ends_with("ld")


@test("truthiness checks")
def test_truthiness():
    that(True).is_true()
    that(False).is_false()
    that(None).is_none()
    that("something").is_not_none()


# Grouped tests with suite
with suite("Collection Operations"):
    @test("list contains item")
    def test_list_contains():
        numbers = [1, 2, 3, 4, 5]
        that(numbers).contains(3)
        that(numbers).does_not_contain(10)
        that(numbers).has_length(5)

    @test("empty collections")
    def test_empty():
        that([]).is_empty()
        that("").is_empty()
        that({}).is_empty()

    @test("dictionary operations")
    def test_dict():
        user = {"name": "John", "age": 30}
        that(user).contains("name")
        that(user["age"]).equals(30)


with suite("Number Comparisons"):
    @test("greater than")
    def test_greater():
        that(10).is_greater_than(5)
        that(3.14).is_greater_than(3)

    @test("less than")
    def test_less():
        that(5).is_less_than(10)
        that(2.5).is_less_than(3)

    @test("between values")
    def test_between():
        that(5).is_between(1, 10)
        that(7.5).is_between(7, 8)


with suite("Type Checking"):
    @test("instance checks")
    def test_instances():
        that("hello").is_instance_of(str)
        that([1, 2, 3]).is_instance_of(list)
        that(42).is_instance_of(int)

    @test("exact type checks")
    def test_exact_types():
        that("hello").has_type(str)
        that(42).has_type(int)
        that(3.14).has_type(float)


with suite("Exception Handling"):
    @test("function raises expected exception")
    def test_raises():
        def divide_by_zero():
            return 1 / 0

        that(divide_by_zero).raises(ZeroDivisionError)

    @test("function does not raise")
    def test_no_raise():
        def safe_function():
            return "safe"

        result = that(safe_function).does_not_raise()
        that(result.value).equals("safe")


# Test with setup and teardown
with suite("Database Tests"):
    def setup():
        """Create a mock database."""
        return {"users": [], "next_id": 1}

    def teardown(db):
        """Clean up the database."""
        db.clear()

    @test("can add user")
    def test_add_user(db):
        user = {"id": db["next_id"], "name": "John"}
        db["users"].append(user)
        db["next_id"] += 1

        that(db["users"]).has_length(1)
        that(db["users"][0]["name"]).equals("John")

    @test("can find user")
    def test_find_user(db):
        # Add a user first
        user = {"id": db["next_id"], "name": "Jane"}
        db["users"].append(user)

        # Find the user
        found = next((u for u in db["users"] if u["name"] == "Jane"), None)
        that(found).is_not_none()
        that(found["name"]).equals("Jane")
