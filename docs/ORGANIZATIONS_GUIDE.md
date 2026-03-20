# Organizations & Multi-Tenancy

## What Are Organizations

Organizations are the multi-tenancy boundary in the system. They separate users into groups — an admin in Organization A cannot see or manage users in Organization B.

Every user (except the system admin) must belong to at least one organization. A user can belong to multiple organizations at the same time.

---

## Users and Organizations

### Who Belongs to an Organization

- Every regular user (`user` role) belongs to one or more organizations
- Every admin (`admin` role) belongs to one or more organizations
- The `systemAdmin` does **not** belong to any organization — they have unrestricted access to everything

### How Users Get Assigned

- When an admin creates a new user and specifies an organization, the user is placed in that organization
- When an admin creates a new user without specifying an organization, the user is automatically placed in the admin's first organization. If the admin belongs to multiple organizations, only the first one is used — the admin should specify the organization explicitly if they want a different one
  ---
- When the system admin creates a user without specifying an organization, the user is placed in the default organization
- Users with the `systemAdmin` role are never assigned to any organization

## The Default Organization

On first startup, the system automatically creates a **default organization** called "Default". It exists so that every user always has at least one organization.

- Created automatically — no manual setup needed
- Users that somehow have no organization are backfilled into it
- The default organization cannot be deleted

---

## Who Can Do What

### System Admin

The system admin can do everything across all organizations:

- Create and delete organizations
- View all organizations and their members
- Add and remove users from any organization
- Create, update, and delete any user regardless of organization

### Admin

An admin is scoped to their own organizations:

- **Can** view organizations they belong to
- **Can** view and manage members within their own organizations
- **Can** add and remove users from organizations they belong to
- **Can** create, update, and delete users who share at least one organization with them
- **Cannot** create or delete organizations
- **Cannot** access data from organizations they don't belong to
- **Cannot** manage users who are only in other organizations

If an admin belongs to both Org A and Org B, they can manage members across both.

### Regular User

A regular user has limited access:

- **Can** view organizations they belong to
- **Can** view and update their own profile
- **Cannot** manage other users
- **Cannot** manage organization membership
- **Cannot** access data from organizations they don't belong to

---

## How Access Is Controlled

Access control happens in two places, one after the other:

1. **At the gateway** — before the request reaches the service, the gateway checks if the user is a member of the organization referenced in the request. If not, the request is blocked immediately.
2. **At the service level** — even if the request passes the gateway, the service checks again before executing the operation. For operations on other users, it checks whether the requester shares at least one organization with the target user.

The system admin bypasses both checks.

This double check means that even if one layer has a bug, the other still protects the data.

---

## Cross-Organization Scenarios

**Admin in Org A tries to view a user in Org B only:**
Blocked. The admin and the target user share no organizations.

**Admin in Org A and Org B tries to view a user in Org B:**
Allowed. They share Org B.

**Admin in Org A tries to add a user to Org B:**
Blocked. The admin is not a member of Org B.

**Admin in Org A and Org B tries to remove a user from Org B:**
Allowed. The admin is a member of the target organization (Org B).

**A user with no organizations tries to access anything:**
Blocked. Non-system-admin users without organizations cannot access any organization-scoped data.