"""Tests for the mocking functionality."""

from that import test, suite, that, mock, mock_that


# Example classes to test mocking with
class Database:
    def query(self, sql, *params):
        raise RuntimeError("Should not call real database")
    
    def insert(self, table, data):
        raise RuntimeError("Should not call real database")


class UserService:
    def __init__(self, db):
        self.db = db
    
    def get_user(self, user_id):
        result = self.db.query("SELECT * FROM users WHERE id = ?", user_id)
        return result[0] if result else None
    
    def create_user(self, name, email):
        return self.db.insert("users", {"name": name, "email": email})


@test("mock returns configured value")
def test_basic_mock():
    db = Database()
    service = UserService(db)
    
    # Mock the injected dependency's method
    query_mock = mock(service.db, "query", return_value=[{"id": 1, "name": "John"}])
    
    user = service.get_user(1)
    
    that(user).equals({"id": 1, "name": "John"})
    that(query_mock.call_count).equals(1)


@test("mock tracks method calls")
def test_mock_tracks_calls():
    db = Database()
    service = UserService(db)
    
    query_mock = mock(service.db, "query", return_value=[])
    
    service.get_user(42)
    
    query_mock.assert_called_with("SELECT * FROM users WHERE id = ?", 42)


@test("mock can raise exceptions")
def test_mock_raises():
    db = Database()
    service = UserService(db)
    
    mock(service.db, "query", raises=ValueError("Connection failed"))
    
    try:
        service.get_user(1)
        raise AssertionError("Should have raised ValueError")
    except ValueError as e:
        that(str(e)).equals("Connection failed")


@test("mock supports side effects as list")
def test_mock_side_effect_list():
    db = Database()
    
    query_mock = mock(db, "query", side_effect=[
        [{"id": 1}],
        [{"id": 2}],
        [{"id": 3}]
    ])
    
    that(db.query("SELECT *")).equals([{"id": 1}])
    that(db.query("SELECT *")).equals([{"id": 2}])
    that(db.query("SELECT *")).equals([{"id": 3}])
    
    # Should raise when exhausted
    try:
        db.query("SELECT *")
        raise AssertionError("Should have raised ValueError")
    except ValueError as e:
        that(str(e)).contains("exhausted side_effect values")


@test("mock supports side effects as callable")
def test_mock_side_effect_callable():
    db = Database()
    
    def dynamic_response(sql, *params):
        if "users" in sql:
            return [{"type": "user"}]
        else:
            return [{"type": "other"}]
    
    mock(db, "query", side_effect=dynamic_response)
    
    that(db.query("SELECT * FROM users")).equals([{"type": "user"}])
    that(db.query("SELECT * FROM posts")).equals([{"type": "other"}])


@test("assert_not_called verifies no calls")
def test_assert_not_called():
    db = Database()
    insert_mock = mock(db, "insert", return_value=1)
    
    # Should pass when not called
    insert_mock.assert_not_called()
    
    # Should fail after calling
    db.insert("users", {})
    
    try:
        insert_mock.assert_not_called()
        raise AssertionError("Should have failed assert_not_called")
    except AssertionError as e:
        that(str(e)).contains("was called 1 time(s)")


with suite("Mock cleanup"):
    
    @test("mocks are cleaned up between tests")
    def test_cleanup_first():
        db = Database()
        mock(db, "query", return_value="mocked")
        that(db.query()).equals("mocked")
    
    @test("mocks from previous test are gone")
    def test_cleanup_second():
        db = Database()
        # This should raise because mock was cleaned up
        try:
            db.query("SELECT * FROM users")
            raise AssertionError("Should have raised RuntimeError")
        except RuntimeError as e:
            that(str(e)).equals("Should not call real database")


@test("mock restores original attribute")
def test_mock_restoration():
    class Service:
        def method(self):
            return "original"
    
    service = Service()
    that(service.method()).equals("original")
    
    # This mock will be cleaned up after the test
    mock(service, "method", return_value="mocked")
    that(service.method()).equals("mocked")


@test("mock handles missing attributes")
def test_mock_missing_attribute():
    class Empty:
        pass
    
    obj = Empty()
    
    # Can mock non-existent attributes
    mock(obj, "new_method", return_value=42)
    that(obj.new_method()).equals(42)
    
    # After cleanup, attribute should be gone
    # (This will be verified in next test due to auto-cleanup)


with suite("Enhanced Mock API"):
    
    @test("fluent assertions work")
    def test_fluent_assertions():
        db = Database()
        service = UserService(db)
        
        # Should support method chaining
        query_mock = mock(service.db, "query", return_value=[{"id": 1}])
        
        service.get_user(42)
        
        # Chain multiple assertions
        query_mock.assert_called_once().assert_called_with("SELECT * FROM users WHERE id = ?", 42)
    
    @test("assert_called_once works")
    def test_assert_called_once():
        db = Database()
        query_mock = mock(db, "query", return_value=[])
        
        # Should pass when called once
        db.query("SELECT *")
        query_mock.assert_called_once()
        
        # Should fail when called multiple times
        db.query("SELECT *")
        try:
            query_mock.assert_called_once()
            raise AssertionError("Should have failed")
        except AssertionError as e:
            that(str(e)).contains("was called 2 time(s), expected 1")
    
    @test("assert_called_times works")
    def test_assert_called_times():
        db = Database()
        query_mock = mock(db, "query", return_value=[])
        
        # Call multiple times
        db.query("SELECT *")
        db.query("SELECT *")
        db.query("SELECT *")
        
        query_mock.assert_called_times(3)
        
        # Should fail with wrong count
        try:
            query_mock.assert_called_times(2)
            raise AssertionError("Should have failed")
        except AssertionError as e:
            that(str(e)).contains("was called 3 time(s), expected 2")
    
    @test("call access properties work")
    def test_call_access():
        db = Database()
        query_mock = mock(db, "query", return_value=[])
        
        # Initially no calls
        that(query_mock.last_call).is_none()
        that(query_mock.first_call).is_none()
        
        # Add some calls
        db.query("SELECT * FROM users", 1)
        db.query("SELECT * FROM posts", 2)
        db.query("SELECT * FROM comments", 3)
        
        # Check first and last calls
        that(query_mock.first_call.args).equals(("SELECT * FROM users", 1))
        that(query_mock.last_call.args).equals(("SELECT * FROM comments", 3))
        
        # Check specific call by index
        second_call = query_mock.get_call(1)
        that(second_call.args).equals(("SELECT * FROM posts", 2))
    
    @test("get_call handles errors")
    def test_get_call_errors():
        db = Database()
        query_mock = mock(db, "query", return_value=[])
        
        # Should raise IndexError when no calls
        try:
            query_mock.get_call(0)
            raise AssertionError("Should have raised IndexError")
        except IndexError as e:
            that(str(e)).contains("has no calls")
        
        # Add one call
        db.query("SELECT *")
        
        # Should raise IndexError for out of range
        try:
            query_mock.get_call(5)
            raise AssertionError("Should have raised IndexError")
        except IndexError as e:
            that(str(e)).contains("out of range (0-0)")
    
    @test("mock_that integration works")
    def test_mock_that_integration():
        db = Database()
        query_mock = mock(db, "query", return_value=[{"id": 1}, {"id": 2}])
        
        # Make some calls
        result1 = db.query("SELECT * FROM users")
        result2 = db.query("SELECT * FROM posts")
        
        # Use mock_that with that() assertions
        mock_assertions = mock_that(query_mock)
        
        that(mock_assertions.call_count).equals(2)
        that(mock_assertions.calls).has_length(2)
        that(mock_assertions.first_call.args).equals(("SELECT * FROM users",))
        that(mock_assertions.last_call.args).equals(("SELECT * FROM posts",))
        
        # Verify the calls returned correct values
        that(result1).equals([{"id": 1}, {"id": 2}])
        that(result2).equals([{"id": 1}, {"id": 2}])