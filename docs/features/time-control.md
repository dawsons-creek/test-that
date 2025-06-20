# Time Control and Replay

Test That includes powerful time control features that make testing time-dependent code deterministic and reliable. No more flaky tests due to timing issues.

## Why Time Control Matters

Time-dependent code is notoriously difficult to test:

=== "Without Time Control"
    ```python
    import datetime
    
    def test_user_creation():
        user = create_user("john@example.com")
        
        # This test is flaky - depends on when it runs
        now = datetime.datetime.now()
        assert user.created_at.date() == now.date()
        
        # This might fail if test runs slowly
        assert (now - user.created_at).seconds < 1
    ```

=== "With Test That Time Control"
    ```python
    from that import that, test, replay
    import datetime
    
    @test("user creation timestamp should be deterministic")
    @replay.time("2024-01-01T12:00:00Z")
    def test_user_creation():
        user = create_user("john@example.com")
        
        # Always predictable - time is frozen
        expected_time = datetime.datetime(2024, 1, 1, 12, 0, 0, tzinfo=datetime.timezone.utc)
        that(user.created_at).equals(expected_time)
    ```

**Test That's time control makes your tests deterministic, fast, and reliable.**

## Basic Time Freezing

### Decorator Usage

```python
from that import that, test, replay
import datetime

@test("order should have correct timestamps")
@replay.time("2024-01-15T10:30:00Z")
def test_order_timestamps():
    order = create_order(items=['laptop', 'mouse'])
    
    # Time is frozen at exactly 2024-01-15 10:30:00 UTC
    expected_time = datetime.datetime(2024, 1, 15, 10, 30, 0, tzinfo=datetime.timezone.utc)
    that(order.created_at).equals(expected_time)
    
    # All time functions return the same frozen time
    that(datetime.datetime.now()).equals(expected_time)
    that(datetime.datetime.utcnow()).equals(expected_time)
```

### Context Manager Usage

```python
@test("multiple operations at same time")
def test_batch_operations():
    with replay.time("2024-01-01T00:00:00Z"):
        # All operations happen at exactly midnight
        user1 = create_user("alice@example.com")
        user2 = create_user("bob@example.com")
        user3 = create_user("charlie@example.com")
        
        midnight = datetime.datetime(2024, 1, 1, 0, 0, 0, tzinfo=datetime.timezone.utc)
        that(user1.created_at).equals(midnight)
        that(user2.created_at).equals(midnight)
        that(user3.created_at).equals(midnight)
```

## Time Format Support

### ISO String Format

```python
# Full ISO format with timezone
@replay.time("2024-01-01T12:00:00Z")
@replay.time("2024-01-01T12:00:00+00:00")
@replay.time("2024-01-01T12:00:00-05:00")  # EST

# Date only (assumes midnight UTC)
@replay.time("2024-01-01")

# Date and time without timezone (assumes UTC)
@replay.time("2024-01-01T12:00:00")
```

### Datetime Object

```python
import datetime

frozen_time = datetime.datetime(2024, 1, 1, 12, 0, 0, tzinfo=datetime.timezone.utc)

@test("using datetime object")
@replay.time(frozen_time)
def test_with_datetime():
    now = datetime.datetime.now()
    that(now).equals(frozen_time)
```

## Real-World Time Testing Scenarios

### Testing Expiration Logic

```python
from that import that, test, suite, replay
import datetime
from dateutil.relativedelta import relativedelta

with suite("Subscription Expiration Tests"):
    
    @test("new subscription should expire in 30 days")
    @replay.time("2024-01-01T00:00:00Z")
    def test_subscription_expiry():
        subscription = create_subscription(plan='monthly')
        
        expected_expiry = datetime.datetime(2024, 1, 31, 0, 0, 0, tzinfo=datetime.timezone.utc)
        that(subscription.expires_at).equals(expected_expiry)
    
    @test("expired subscription should be inactive")
    @replay.time("2024-02-01T00:00:00Z")  # After expiry
    def test_expired_subscription():
        # Create subscription in the past
        with replay.time("2024-01-01T00:00:00Z"):
            subscription = create_subscription(plan='monthly')
        
        # Back to "present" - subscription should be expired
        that(subscription.is_active()).is_false()
        that(subscription.is_expired()).is_true()
```

### Testing Time-Based Business Logic

```python
with suite("Business Hours Tests"):
    
    @test("orders during business hours should process immediately")
    @replay.time("2024-01-15T14:00:00Z")  # Monday 2 PM UTC
    def test_business_hours_processing():
        order = create_order(items=['laptop'])
        
        # Should process immediately during business hours
        that(order.status).equals('processing')
        that(order.estimated_delivery).is_not_none()
    
    @test("orders after hours should queue for next day")
    @replay.time("2024-01-15T22:00:00Z")  # Monday 10 PM UTC
    def test_after_hours_processing():
        order = create_order(items=['laptop'])
        
        # Should queue for next business day
        that(order.status).equals('queued')
        
        # Estimated processing should be next business day at 9 AM
        expected_processing = datetime.datetime(2024, 1, 16, 9, 0, 0, tzinfo=datetime.timezone.utc)
        that(order.estimated_processing_at).equals(expected_processing)
```

### Testing Recurring Events

```python
@test("daily report should generate at midnight")
@replay.time("2024-01-01T00:00:00Z")
def test_daily_report_generation():
    # Trigger daily report generation
    report = generate_daily_report()
    
    that(report.date).equals(datetime.date(2024, 1, 1))
    that(report.generated_at).equals(datetime.datetime(2024, 1, 1, 0, 0, 0, tzinfo=datetime.timezone.utc))

@test("weekly report should include full week")
@replay.time("2024-01-07T23:59:59Z")  # End of first week
def test_weekly_report():
    report = generate_weekly_report()
    
    that(report.week_start).equals(datetime.date(2024, 1, 1))
    that(report.week_end).equals(datetime.date(2024, 1, 7))
    that(report.days_included).equals(7)
```

## Advanced Time Control Patterns

### Time Progression Within Tests

```python
@test("user session should timeout after inactivity")
def test_session_timeout():
    # Start at a specific time
    with replay.time("2024-01-01T12:00:00Z"):
        session = create_user_session("user123")
        that(session.is_active()).is_true()
    
    # Move forward 29 minutes - should still be active
    with replay.time("2024-01-01T12:29:00Z"):
        that(session.is_active()).is_true()
    
    # Move forward 31 minutes - should timeout
    with replay.time("2024-01-01T12:31:00Z"):
        that(session.is_active()).is_false()
        that(session.timeout_reason).equals("inactivity")
```

### Testing Time Zones

```python
from that import that, test, suite, replay
import pytz

with suite("Timezone Handling"):
    
    @test("event should respect user timezone")
    @replay.time("2024-01-01T17:00:00Z")  # 5 PM UTC
    def test_user_timezone():
        # User in EST (UTC-5)
        user = create_user("john@example.com", timezone="America/New_York")
        event = schedule_event(user, "Meeting", duration_hours=1)
        
        # Event should show in user's local time
        est = pytz.timezone('America/New_York')
        expected_local_time = datetime.datetime(2024, 1, 1, 12, 0, 0)  # 12 PM EST
        expected_local_time = est.localize(expected_local_time)
        
        that(event.local_start_time).equals(expected_local_time)
    
    @test("global event should work across timezones")
    @replay.time("2024-01-01T15:00:00Z")  # 3 PM UTC
    def test_global_event():
        users = [
            create_user("alice@example.com", timezone="America/New_York"),    # EST
            create_user("bob@example.com", timezone="Europe/London"),        # GMT
            create_user("charlie@example.com", timezone="Asia/Tokyo"),       # JST
        ]
        
        global_event = create_global_event("Product Launch", users)
        
        # All users should see the same UTC time
        utc_time = datetime.datetime(2024, 1, 1, 15, 0, 0, tzinfo=datetime.timezone.utc)
        that(global_event.utc_start_time).equals(utc_time)
        
        # But different local times
        that(global_event.get_local_time(users[0])).contains("10:00")  # 10 AM EST
        that(global_event.get_local_time(users[1])).contains("15:00")  # 3 PM GMT
        that(global_event.get_local_time(users[2])).contains("00:00")  # Midnight JST (next day)
```

## Integration with HTTP Recording

Time control works seamlessly with HTTP recording:

```python
@test("API call should include correct timestamp")
@replay(time="2024-01-01T12:00:00Z", http="api_with_timestamp")
def test_api_timestamp():
    # Both time is frozen AND HTTP calls are recorded/replayed
    response = api_client.create_post(
        title="New Post",
        content="This is a test post"
    )
    
    # The API response will be consistent because:
    # 1. Time is frozen, so timestamps are predictable
    # 2. HTTP response is recorded/replayed
    that(response['created_at']).equals("2024-01-01T12:00:00Z")
    that(response['id']).is_instance_of(int)
```

## Testing Date Calculations

```python
with suite("Date Calculation Tests"):
    
    @test("age calculation should be accurate")
    @replay.time("2024-01-01T00:00:00Z")
    def test_age_calculation():
        # Person born on 1990-01-01
        birthdate = datetime.date(1990, 1, 1)
        age = calculate_age(birthdate)
        
        # On 2024-01-01, they should be exactly 34
        that(age).equals(34)
    
    @test("business days calculation should exclude weekends")
    @replay.time("2024-01-15T00:00:00Z")  # Monday
    def test_business_days():
        start_date = datetime.date(2024, 1, 15)  # Monday
        
        # 5 business days from Monday should be next Monday
        end_date = add_business_days(start_date, 5)
        expected_end = datetime.date(2024, 1, 22)  # Next Monday
        
        that(end_date).equals(expected_end)
        that(end_date.weekday()).equals(0)  # Monday
    
    @test("holiday calculation should skip holidays")
    @replay.time("2024-12-23T00:00:00Z")  # Monday before Christmas
    def test_holiday_calculation():
        start_date = datetime.date(2024, 12, 23)
        
        # 3 business days should skip Christmas and weekend
        end_date = add_business_days(start_date, 3, skip_holidays=True)
        expected_end = datetime.date(2024, 12, 30)  # Monday after Christmas
        
        that(end_date).equals(expected_end)
```

## Performance and Caching Tests

```python
@test("cache should expire after TTL")
def test_cache_expiration():
    cache = TimeBasedCache(ttl_seconds=300)  # 5 minute TTL
    
    # Set cache at specific time
    with replay.time("2024-01-01T12:00:00Z"):
        cache.set("key1", "value1")
        that(cache.get("key1")).equals("value1")
    
    # 4 minutes later - should still be cached
    with replay.time("2024-01-01T12:04:00Z"):
        that(cache.get("key1")).equals("value1")
    
    # 6 minutes later - should be expired
    with replay.time("2024-01-01T12:06:00Z"):
        that(cache.get("key1")).is_none()

@test("rate limiter should reset after time window")
def test_rate_limiter():
    limiter = RateLimiter(max_requests=5, window_seconds=60)
    
    with replay.time("2024-01-01T12:00:00Z"):
        # Use up all requests
        for i in range(5):
            that(limiter.allow_request("user123")).is_true()
        
        # 6th request should be denied
        that(limiter.allow_request("user123")).is_false()
    
    # 61 seconds later - should reset
    with replay.time("2024-01-01T12:01:01Z"):
        that(limiter.allow_request("user123")).is_true()
```

## Best Practices

### 1. Use Realistic Times
```python
# Good - realistic business scenario
@replay.time("2024-01-15T14:30:00Z")  # Monday afternoon

# Less realistic - might miss edge cases
@replay.time("2000-01-01T00:00:00Z")
```

### 2. Test Edge Cases
```python
# Test end of month
@replay.time("2024-01-31T23:59:59Z")

# Test leap year
@replay.time("2024-02-29T12:00:00Z")

# Test daylight saving time transitions
@replay.time("2024-03-10T07:00:00Z")  # DST begins in US
```

### 3. Be Explicit About Timezones
```python
# Good - explicit timezone
@replay.time("2024-01-01T12:00:00Z")

# Can be ambiguous
@replay.time("2024-01-01T12:00:00")
```

### 4. Test Time Progression When Needed
```python
@test("should handle time-based state changes")
def test_time_progression():
    # Start state
    with replay.time("2024-01-01T09:00:00Z"):
        task = create_scheduled_task(run_at="2024-01-01T10:00:00Z")
        that(task.status).equals("scheduled")
    
    # After scheduled time
    with replay.time("2024-01-01T10:01:00Z"):
        task.check_and_run()
        that(task.status).equals("completed")
```

## Common Patterns

### Testing Cron Jobs and Scheduled Tasks
```python
@test("daily cleanup should run at midnight")
@replay.time("2024-01-02T00:00:00Z")
def test_daily_cleanup():
    cleanup_job = DailyCleanupJob()
    result = cleanup_job.run()
    
    that(result.cleaned_records).is_greater_than(0)
    that(result.run_date).equals(datetime.date(2024, 1, 2))
```

### Testing Audit Trails
```python
@test("audit log should capture exact timestamps")
@replay.time("2024-01-01T15:30:45Z")
def test_audit_logging():
    user = authenticate_user("john@example.com")
    
    audit_entry = get_latest_audit_entry()
    expected_time = datetime.datetime(2024, 1, 1, 15, 30, 45, tzinfo=datetime.timezone.utc)
    
    that(audit_entry.timestamp).equals(expected_time)
    that(audit_entry.action).equals("user_login")
    that(audit_entry.user_id).equals(user.id)
```

## Next Steps

- **[HTTP Recording](http-recording.md)** - Combine time control with HTTP recording
- **[Real Examples](../examples/web-api-testing.md)** - See time control in real applications
- **[API Reference](../api/replay.md)** - Complete time control API documentation
