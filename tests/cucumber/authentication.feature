@cucumber @identity @requirement_AUTH-001
Feature: Cucumber.js compatibility for authentication
  Generated Gherkin can execute through Cucumber.js as well as Behave.

  @smoke
  Scenario: Valid user login returns tokens
    Given the demo API is healthy
    And a unique registered Cucumber user
    When the Cucumber user submits valid credentials
    Then access and refresh tokens are returned by the API

  @authorization
  Scenario: Standard Cucumber user cannot access admin audit
    Given the demo API is healthy
    And a unique registered Cucumber user
    When the Cucumber user logs in and requests admin audit
    Then the Cucumber user receives forbidden
