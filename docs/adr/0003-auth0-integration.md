# ADR 0003: Auth0 Authentication and Role-Based Access Control

## Status
Accepted

## Context
Our application requires secure authentication and role-based authorization for different types of actors (Producers, Advisors, and Admins). Implementing credentials storage, password reset flows, secure token rotation, and single sign-on from scratch increases security risks and maintenance overhead.

We need a solution that delegates identity management to a trusted provider while maintaining:
1. Fast, local validation of credentials.
2. Local database user synchronization to maintain references for campaigns, plots, and recommendations.
3. Declarative role enforcement at the router level.

## Decision
We integrate **Auth0** as our primary Identity Provider (IdP) and implement the following patterns:

1. **Token Validation**: The API uses [src/core/auth.py](file:///C:/Proyectos/Api-AgricultureHandling/src/core/auth.py) to locally verify incoming JWT Bearer tokens. It retrieves the JSON Web Key Set (JWKS) from Auth0's `/.well-known/jwks.json` and caches it to validate signatures without making network requests on every request.
2. **User Synchronization**: On authentication, we extract the `sub` claim (Auth0 user ID). If the user does not exist in the local database, we fetch their profile from Auth0's `/userinfo` endpoint and provision them in our local database with the roles provided.
3. **Custom Claims for Roles**: User roles are managed inside Auth0 and injected into the Access Token as a custom claim: `https://api.agriculture-handling.com/roles`.
4. **Role Enforcement**: We use FastAPI dependency injection with `check_role` to secure routes based on database user roles:
   ```python
   @router.post("/", dependencies=[Depends(check_role([UserRole.ADMIN, UserRole.ADVISOR]))])
   async def create_recommendation(...):
   ```

## Consequences

### Positive
* **High Security**: Passwords, MFA, and OAuth2 standard compliance are handled entirely by Auth0.
* **Performance**: Local JWT validation using JWKS minimizes request latency.
* **Declarative Security**: Clear and readable endpoint decoration makes auditing route access straightforward.

### Negative
* **External Dependency**: If Auth0 is down, users cannot authenticate (though token validation for existing sessions remains operational).
* **Configuration Overhead**: Requires configuring custom Actions/Rules in the Auth0 dashboard to append roles to access tokens.
