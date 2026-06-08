# Test Cases

The project includes comprehensive testing for the AI-powered ticket classification workflow.

---

## Covered Scenarios

### ✅ Authentication Issues
- Login Failure
- Password Reset
- MFA Verification Issues
- Account Recovery

### ✅ Billing Issues
- Refund Requests
- Payment Failures
- Invoice Requests
- Subscription Problems

### ✅ Technical Issues
- Application Bugs
- Performance Degradation
- System Crashes
- Integration Failures

### ✅ Network Issues
- VPN Connectivity Problems
- DNS Resolution Failures
- Firewall Restrictions
- Network Performance Issues

### ✅ Account Issues
- Profile Updates
- Access Requests
- Account Locked
- Permission Changes

---

## Example Test Cases

| Test Case ID | Ticket Title | Expected Category | Expected Priority |
|-------------|-------------|------------------|------------------|
| TC001 | Unable to login after password reset | Authentication | High |
| TC002 | MFA code not received | Authentication | High |
| TC003 | Account recovery email not received | Authentication | High |
| TC004 | Payment deducted twice | Billing | High |
| TC005 | Refund not received after cancellation | Billing | Medium |
| TC006 | Subscription renewed unexpectedly | Billing | Medium |
| TC007 | Application crashes on startup | Technical | Critical |
| TC008 | System unavailable for all users | Technical | Critical |
| TC009 | Slow application response | Technical | Medium |
| TC010 | Third-party integration failure | Technical | High |
| TC011 | VPN connection keeps disconnecting | Network | Medium |
| TC012 | DNS resolution failure | Network | High |
| TC013 | Firewall blocking application traffic | Network | High |
| TC014 | Unable to connect to company network | Network | High |
| TC015 | Need access to admin dashboard | Account | Medium |
| TC016 | Account locked after multiple login attempts | Account | High |
| TC017 | Missing permissions for assigned module | Account | Medium |
| TC018 | Profile information update request | Account | Medium |

---

## Testing Framework

| Component | Tool Used |
|------------|------------|
| Unit Testing | Pytest |
| API Testing | FastAPI TestClient |
| Mocking | Mocked Ollama Responses |
| Endpoint Validation | FastAPI Testing Utilities |
| Database Testing | SQLAlchemy Integration Tests |
| Code Coverage | pytest-cov |

---

## Validation Metrics

- Category Classification Accuracy
- Priority Prediction Accuracy
- Confidence Score Evaluation
- Response Time Monitoring
- Retry Mechanism Validation
- Database Logging Validation
- API Response Validation

---

## Sample Pytest Command

```bash
pytest tests/
```

### Run with Coverage

```bash
pytest --cov=app tests/
```

---

## Expected Results

| Metric | Expected Result |
|----------|----------------|
| Classification Accuracy | > 90% |
| Average Confidence Score | > 0.85 |
| API Response Time | < 2 Seconds |
| Endpoint Availability | > 99% |
| Invalid Input Handling | Successful |
| Fallback Classification | Successful |
| Database Logging | Verified |
| Retry Mechanism | Working |
| API Validation | Passed |

---

## Test Status Summary

| Module | Status |
|---------|---------|
| Authentication Classification | ✅ Passed |
| Billing Classification | ✅ Passed |
| Technical Classification | ✅ Passed |
| Network Classification | ✅ Passed |
| Account Classification | ✅ Passed |
| API Endpoint Testing | ✅ Passed |
| Database Integration Testing | ✅ Passed |
| Error Handling Testing | ✅ Passed |
| Retry Logic Testing | ✅ Passed |
| Performance Testing | ✅ Passed |