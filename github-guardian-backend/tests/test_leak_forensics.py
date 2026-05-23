from src.services.leak_forensics import scan_for_secrets, calculate_entropy

def test_specific_secrets():
    # Test AWS Access Key
    res = scan_for_secrets('aws_id = "AKIAIOSFODNN7EXAMPLE"')
    assert any(x["pattern_matched"] == "AWS Access Key ID" for x in res)

    # Test AWS Secret Key
    res = scan_for_secrets('aws_secret_access_key = "wJalrXUtn' + 'FEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"')
    assert any(x["pattern_matched"] == "AWS Secret Key" for x in res)

    # Test GitHub Token
    res = scan_for_secrets('my_token = "ghp_' + '123456789012345678901234567890123456"')
    assert any(x["pattern_matched"] == "GitHub Token" for x in res)

    # Test Slack Webhook
    res = scan_for_secrets('url = "https://hooks.slack.com/services/' + 'T12345678/' + 'B12345678/' + 'aBcDeFgHiJkLmNoPqRsTuVwX"')
    assert any(x["pattern_matched"] == "Slack Webhook" for x in res)

    # Test Slack Token
    res = scan_for_secrets('token = "xoxb-' + '1234567890-123456789012-aBcDeFgHiJkLmNoPqRsTuVwX"')
    assert any(x["pattern_matched"] == "Slack Token" for x in res)

    # Test Stripe API Key
    res = scan_for_secrets('stripe_key = "sk_live_' + '123456789012345678901234"')
    assert any(x["pattern_matched"] == "Stripe API Key" for x in res)

    # Test Google API Key
    res = scan_for_secrets('key = "AIzaSyA' + '1B2C3D4E5F6G7H8I9J0K1L2M3N4O5P6Q"')
    assert any(x["pattern_matched"] == "Google API Key" for x in res)

    # Test OpenAI API Key
    res = scan_for_secrets('openai_key = "sk-' + '1234567890abcdef1234567890abcdef12345678"')
    assert any(x["pattern_matched"] == "OpenAI API Key" for x in res)

    # Test Twilio Account SID
    res = scan_for_secrets('sid = "AC' + '1234567890abcdef1234567890abcdef"')
    assert any(x["pattern_matched"] == "Twilio Account SID" for x in res)

    # Test Database URL
    res = scan_for_secrets('conn = "postgres://user:super_secret_pwd@localhost:5432/mydb"')
    assert any(x["pattern_matched"] == "Database URL" for x in res)

    # Test Private Key
    res = scan_for_secrets('-----BEGIN RSA PRIVATE KEY-----\n...\n-----END RSA PRIVATE KEY-----')
    assert any(x["pattern_matched"] == "Private Key" for x in res)

def test_generic_high_entropy_secrets():
    # High entropy variable assignment should be flagged
    res = scan_for_secrets('custom_api_secret = "4a8e2b9c7d8e9f0a2b3c4d5e6f7a8b9c"')
    assert any("High-Entropy Secret" in x["pattern_matched"] for x in res)

    # Low entropy/safe string should NOT be flagged
    res = scan_for_secrets('my_safe_password = "passwordpassword"')
    assert not any("High-Entropy Secret" in x["pattern_matched"] for x in res)

    # String with non-secret variable name should NOT be flagged
    res = scan_for_secrets('some_random_text = "4a8e2b9c7d8e9f0a2b3c4d5e6f7a8b9c"')
    assert not any("High-Entropy Secret" in x["pattern_matched"] for x in res)

if __name__ == "__main__":
    test_specific_secrets()
    test_generic_high_entropy_secrets()
    print("All tests passed successfully!")
