---
description: How to run Django management commands on Render production database
---

# Running Django Management Commands on Render Production

## Method 1: Render Dashboard Shell (Easiest)

1. **Go to Render Dashboard**
   - Navigate to https://dashboard.render.com
   - Select your `daily-task-review` web service

2. **Open Shell**
   - Click on the **Shell** tab in the left sidebar
   - This opens a terminal connected to your production server

3. **Run the command**

   ```bash
   python manage.py fix_active_days
   ```

4. **Verify the output** - you should see something like:

   ```
   User "john" has 3 active days!
     ✓ Keeping 2026-01-28 as active
     ✗ Deactivated 2026-01-27
     ✗ Deactivated 2026-01-26

   ✅ Fixed 2 duplicate active days!
   ```

---

## Method 2: Render CLI (For Automation)

1. **Install Render CLI**

   ```bash
   # Windows (PowerShell)
   iwr https://cli-artifacts.render.com/v1/install.ps1 -useb | iex

   # Or via npm
   npm install -g @render/cli
   ```

2. **Login to Render**

   ```bash
   render login
   ```

3. **Find your service**

   ```bash
   render services list
   ```

4. **Run the command**
   ```bash
   render run -s daily-task-review python manage.py fix_active_days
   ```

---

## Method 3: SSH (If Enabled)

If you have SSH access enabled on Render:

```bash
render ssh daily-task-review
python manage.py fix_active_days
```

---

## Method 4: Add to Migration Script (Automatic)

If you want this to run automatically on every deployment, update your `render.yaml`:

```yaml
services:
  - type: web
    name: daily-task-review
    env: python
    buildCommand: |
      pip install -r requirements.txt
      python manage.py collectstatic --noinput
      python manage.py migrate
      python manage.py fix_active_days  # ← Add this line
    startCommand: gunicorn daily_task_review.wsgi:application
```

**⚠️ Warning**: Only do this if you want it to run on EVERY deployment!

---

## Method 5: One-Time Background Job

Create a one-time job in Render:

1. Go to Render Dashboard
2. Click **New** → **Background Worker**
3. Connect your repository
4. Set the **Start Command** to:
   ```bash
   python manage.py fix_active_days && sleep 3600
   ```
5. Deploy and it will run once

---

## Best Practice: Run Before Migration

**Recommended deployment sequence:**

```yaml
buildCommand: |
  pip install -r requirements.txt
  python manage.py collectstatic --noinput
  python manage.py fix_active_days  # ← Fix data FIRST
  python manage.py migrate          # ← Then apply constraint
```

This ensures:

1. Fix any existing duplicate active days
2. Then apply the database constraint
3. Prevents constraint violation errors

---

## Checking Production Database Directly

If you want to verify the fix without running the command:

```bash
# In Render Shell
python manage.py shell

# Then in Python shell:
from django.contrib.auth.models import User
from tasks.models import Day

for user in User.objects.all():
    active = Day.objects.filter(user=user, is_active=True)
    if active.count() > 1:
        print(f"❌ {user.username} has {active.count()} active days!")
    else:
        print(f"✅ {user.username} is OK")
```

---

## Troubleshooting

**If you get "Command not found":**

- Make sure you've committed and pushed the new files:
  - `tasks/management/__init__.py`
  - `tasks/management/commands/__init__.py`
  - `tasks/management/commands/fix_active_days.py`

**If you get database connection errors:**

- Make sure your `DATABASE_URL` environment variable is set correctly in Render
- Check that your database is running

**If migration fails with constraint error:**

- Run `fix_active_days` BEFORE running migrations
- The constraint won't apply if there's existing violating data
