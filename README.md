# SeaBounty: Find Fresh Seafood Near You

Full-stack Django web app (Django templates + PostgreSQL/Supabase) that connects locals and tourists
on Bantayan Island with fresh seafood stalls. CSIT327-G5 · Information Management 2.

## Features

**Project Development 1 – Account Feature**
Registration, login/logout, role-based dashboards (Buyer, Vendor, Admin) and user profile.

**Project Development 2 – Core Feature: Stalls & Daily Catch Updates**
The main purpose of SeaBounty: vendors list their stalls and post what seafood they have and its price,
and buyers search that information to avoid wasted trips.

| Role   | What they can do |
|--------|------------------|
| Vendor | Create, edit and delete **their own** stalls; post, edit and delete **their own** catch updates (seafood type + price per kg) for their open stalls |
| Buyer  | Browse stalls, view stall pages, and search/filter posted seafood by type, stall or place |
| Admin  | See every stall (including closed ones), edit/delete any stall, and remove any catch update |

Rules enforced (see SDD): unique stall names (BR-03), price per kg must be greater than zero (BR-04, also a
database CHECK constraint), updates must belong to a valid active stall and seafood category (BR-06),
deleting a stall removes its updates (ON DELETE CASCADE).

Data model (PostgreSQL tables): `users`, `stalls`, `seafood_categories`, `catch_updates`.
Seafood categories (Crab, Tuna, Squid, ...) are inserted automatically by a migration.

## Setup (Windows Command Prompt)

```cmd
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Edit `.env` with your PostgreSQL or Supabase details (never commit this file), then:

```cmd
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Open http://127.0.0.1:8000/

## Roles and test accounts

* Registering lets you choose **Buyer** or **Vendor**.
* The account made with `createsuperuser` is the **Administrator**.

## Tests

```cmd
python manage.py test
```

(Tests create a temporary database, so your database user needs permission to create databases.)

## Branching

`main` (stable) ← `develop` (integration) ← `feature/stall-management`, `feature/catch-updates`
