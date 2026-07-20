# QP-TC-AUTH-003-002: Refresh token replay was accepted

**Severity:** major  
**Priority:** high  
**Component:** identity  
**Build/commit:** local-demo  
**Related test:** TC-AUTH-003-002

## Summary

A previously rotated refresh token returned a new token pair instead of being rejected.

## Steps to reproduce

1. Register and log in a standard user.
2. Refresh once and retain the original refresh token.
3. Submit the original token again.

## Expected

The replay returns 401.

## Actual

The replay returned 200 while the intentional non-rotation demo flag was enabled.

## Suspected cause and owner

Refresh rotation was disabled by a controlled demonstration flag — security/backend.

This is a sample artifact, not evidence of a default product defect.

