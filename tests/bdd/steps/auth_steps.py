from behave import given, then, when

USER = {"email": "user@example.com", "password": "StrongPass!123", "display_name": "BDD User"}


@given("a registered standard user")
def registered(context):
    assert context.client.post("/api/register", json=USER).status_code == 201


@given("a logged-in standard user")
def logged_in(context):
    registered(context)
    context.tokens = context.client.post("/api/login", json=USER).json()


@when("the user logs in with the valid password")
def valid_login(context):
    context.response = context.client.post("/api/login", json=USER)


@when('the user logs in with email "{email}" and password "{password}"')
def invalid_login(context, email, password):
    context.response = context.client.post(
        "/api/login", json={"email": email, "password": password}
    )


@when("the user requests the admin audit endpoint")
def admin_request(context):
    context.response = context.client.get(
        "/api/admin/audit", headers={"Authorization": f"Bearer {context.tokens['access_token']}"}
    )


@then("access and refresh tokens are returned")
def tokens_returned(context):
    assert context.response.status_code == 200
    assert {"access_token", "refresh_token"} <= context.response.json().keys()


@then("login is rejected")
def rejected(context):
    assert context.response.status_code == 401


@then("access is forbidden")
def forbidden(context):
    assert context.response.status_code == 403
