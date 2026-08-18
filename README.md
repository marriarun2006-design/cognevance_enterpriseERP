# Cognevance Enterprise ERP & Analytics Platform

## Overview
A modular enterprise resource planning prototype covering employees, inventory, sales, finance and analytics.

## Modules
- Secure authentication and authorization
- Employee management
- Inventory management
- Sales records
- Finance records
- Analytics dashboard
- REST summary API
- Responsive web interface

## Roles
- `employee`: dashboard, sales and analytics
- `manager`: administrative modules
- `admin`: administrative modules

For a real production deployment, replace demo role selection with controlled administrative provisioning and use a production database.

## Run
```bash
python -m venv venv
# Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```
Open `http://127.0.0.1:5000`.

## Repository
`cognevance_enterpriseERP`

## API
`GET /api/summary` returns revenue, expenses, profit, employee count and inventory count for an authenticated user.

## Production notes
Set a strong `SECRET_KEY`, use PostgreSQL/MySQL, configure HTTPS, add CSRF protection, rate limiting, secure cookies and centralized logging before production use.

## Deployment
Use Render, Railway or PythonAnywhere and add the final URL after deployment.

