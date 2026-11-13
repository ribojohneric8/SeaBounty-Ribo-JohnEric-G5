# SeaBounty: Find Fresh Seafood Near You

Full-stack Django web app (Django templates + PostgreSQL/Supabase) that connects locals and tourists
on Bantayan Island with fresh seafood stalls. CSIT327-G5 · Information Management 2.

**Project Development 1 – Account Feature:** registration, login/logout, role-based dashboards
(Buyer, Vendor, Admin) and user profile.

## Setup

```bash
# 1. Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
source venv/bin/activate       # macOS/Linux

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env           # then edit .env with your PostgreSQL/Supabase credentials

# 4. Create tables and an admin account
python manage.py migrate
python manage.py createsuperuser   # this account gets the ADMIN role

# 5. Run
python manage.py runserver
```

Open http://127.0.0.1:8000/

## Roles

| Role   | How to get it                        | Dashboard            |
|--------|--------------------------------------|----------------------|
| BUYER  | Choose "Buyer" at registration       | `/dashboard/buyer/`  |
| VENDOR | Choose "Vendor" at registration      | `/dashboard/vendor/` |
| ADMIN  | `createsuperuser` or Django admin    | `/dashboard/admin/`  |

Users who open another role's dashboard URL are sent back to their own dashboard.

## Tests

```bash
python manage.py test accounts
```

(Tests create a temporary database, so your PostgreSQL user needs permission to create databases.)
