# Specification: Testing Suite

## Purpose
The purpose of this specification is to define the testing framework and capabilities required to run automated tests checking API endpoints, authorization rules, campaign/plot permissions, and mock external API integrations.

## Requirements and Scenarios

### Requirement 1: Authentication & Authorization Mocking
The testing framework MUST support mocking authentication and authorization for different roles (e.g., ADMIN, ADVISOR, FARMER) to verify access controls on secured API endpoints.

#### Scenario 1.1: Verify authorized admin access
- **Given** an API endpoint configured to require ADMIN privileges
- **When** a request is made with a mocked ADMIN authentication token
- **Then** the server SHALL respond with a 200 OK status code and the expected resource.

#### Scenario 1.2: Verify unauthorized farmer access to admin endpoints
- **Given** an API endpoint configured to require ADMIN privileges
- **When** a request is made with a mocked FARMER authentication token
- **Then** the server MUST respond with a 403 Forbidden status code.

---

### Requirement 2: Campaigns Access Control
Farmers MUST NOT be able to view or manage campaigns belonging to other farmers. They SHALL only access campaigns associated with their own user account.

#### Scenario 2.1: Farmer viewing their own campaign
- **Given** an authenticated farmer who owns Campaign A
- **When** the farmer requests Campaign A details
- **Then** the API MUST return the details of Campaign A with a 200 OK status.

#### Scenario 2.2: Farmer trying to view another farmer's campaign
- **Given** an authenticated farmer who does not own Campaign B
- **When** the farmer requests Campaign B details
- **Then** the API MUST return a 403 Forbidden or 404 Not Found status code to restrict access.

---

### Requirement 3: Plots & Recommendations Permissions
Advisors MUST be allowed to create recommendations for any plot, while farmers SHOULD only be allowed to view recommendations made for plots they own.

#### Scenario 3.1: Advisor creating a recommendation
- **Given** an authenticated advisor
- **When** the advisor submits a recommendation for Plot X
- **Then** the API SHALL create the recommendation and return a 201 Created status code.

#### Scenario 3.2: Farmer viewing recommendations for their own plot
- **Given** an authenticated farmer who owns Plot X with Recommendation Y
- **When** the farmer requests the recommendations for Plot X
- **Then** the API MUST return Recommendation Y with a 200 OK status.

#### Scenario 3.3: Farmer trying to create a recommendation
- **Given** an authenticated farmer
- **When** the farmer attempts to create a recommendation for Plot X
- **Then** the API MUST reject the request with a 403 Forbidden status code.

---

### Requirement 4: Mock External Integrations
All calls to external systems, specifically the Calendar and Weather APIs, MUST be mocked during test execution to prevent live HTTP requests and ensure test reproducibility.

#### Scenario 4.1: Retrieve crop recommendation trigger weather check
- **Given** a mocked Weather API returning a specific forecast
- **When** a client requests an agricultural plot report that triggers weather integration
- **Then** the application MUST use the mocked weather data instead of calling the live service, returning a 200 OK status.

#### Scenario 4.2: Creating plot activity syncs calendar
- **Given** a mocked Calendar API
- **When** a client schedules a new plot maintenance task
- **Then** the application SHALL verify that the calendar mock was called with the correct event parameters.
