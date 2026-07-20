@identity @requirement_AUTH-001
Feature: User authentication and authorization
  Registered users need safe token-based access to protected resources.

  @smoke @positive
  Scenario: Valid login
    Given a registered standard user
    When the user logs in with the valid password
    Then access and refresh tokens are returned

  @negative
  Scenario Outline: Invalid login input
    Given a registered standard user
    When the user logs in with email "<email>" and password "<password>"
    Then login is rejected

    Examples:
      | email            | password       |
      | user@example.com | wrong-password |
      | none@example.com | StrongPass!123 |

  @authorization @requirement_AUTH-005
  Scenario: Standard user cannot access admin audit
    Given a logged-in standard user
    When the user requests the admin audit endpoint
    Then access is forbidden

