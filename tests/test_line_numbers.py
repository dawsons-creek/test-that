"""Test file to demonstrate line number test selection."""

from test_that import suite, test, that


@test("test at line 7")
def test_first():
    that(1 + 1).equals(2)


@test("test at line 12")
def test_second():
    that("hello").starts_with("he")


@test("test at line 17")
def test_third():
    that([1, 2, 3]).has_length(3)


with suite("Math Suite"):
    @test("addition test at line 23")
    def test_addition():
        that(5 + 3).equals(8)

    @test("subtraction test at line 28")
    def test_subtraction():
        that(10 - 4).equals(6)

    @test("multiplication test at line 33")
    def test_multiplication():
        that(6 * 7).equals(42)


with suite("String Suite"):
    @test("string contains at line 39")
    def test_string_contains():
        that("hello world").contains("world")

    @test("string matching at line 44")
    def test_string_match():
        that("test123").matches(r"\w+\d+")


@test("test at line 49")
def test_last():
    that(True).is_true()
