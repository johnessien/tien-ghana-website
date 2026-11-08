# TIEN Ghana website: handover

This is the TIEN Ghana website: an immersive 3D front-end on a Django back-end. Visitors can join the network,
contact the team, send partnership enquiries, subscribe for updates and (once Paystack is connected) donate.
Everything the team needs to change day to day is done in the **admin area** (`/secretariat-admin/`), not in code.

- What still needs real content before launch: see **CONTENT-TODO.md**
- For developers: see **README.md**

---

## Deploy on Render and Neon

This puts the website online for free, using three accounts:

| Service | What it does | Cost |
|---|---|---|
| **GitHub** | Stores the website's code. Render reads it from here. | Free |
| **Neon** | The database: every sign-up, message and setting is saved here. | Free plan |
| **Render** | Runs the website and gives it a web address. | Free plan |

Allow about 30 minutes the first time. You do not need to install anything on your computer.

### Before you start

Have these ready:

1. Access to the GitHub account that holds the **tien-ghana-website** repository.
2. A username, email and **strong password** for the website's admin account. The password must be at least
   8 characters and not a common word or all numbers, e.g. `Kente-Loom-2026!`. Keep it somewhere safe.

### Step 1: Create the database on Neon

1. Go to **neon.tech** and click **Sign up**. Choose **Continue with GitHub** (simplest) or use an email.
2. When asked to create a project:
   - **Project name:** `tien-ghana`
   - **Postgres version:** leave the default
   - **Region:** choose **AWS Europe Central 1 (Frankfurt)**. This is the closest to Ghana and matches the Render
     region used below. Keeping both in Frankfurt makes the site faster.
   - Click **Create project**.
3. On the project dashboard, click **Connect** (top right).
4. In the window that opens, make sure **Connection pooling** is switched **on**, then click **Copy snippet**
   (or the copy icon next to the connection string). It looks like this:
   `postgresql://neondb_owner:AbC123...@ep-something-pooler.eu-central-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require`
5. Paste it into a private note for now. **Treat it like a password**: anyone with it can read the database.

### Step 2: Create the website on Render

1. Go to **render.com** and click **Get Started**. Choose **GitHub** to sign up, and allow Render to see the
   **tien-ghana-website** repository when GitHub asks (you can pick "Only select repositories").
2. In the Render dashboard, click **New +** (top right), then **Blueprint**.
3. Choose the **tien-ghana-website** repository and click **Connect**.
4. Render reads the file `render.yaml` and shows one service called **tien-ghana**. Give the Blueprint a name
   (e.g. `TIEN Ghana`).
5. Render now asks for the values it cannot fill in by itself. Enter:

   | Setting | What to enter |
   |---|---|
   | `DATABASE_URL` | The Neon connection string from Step 1 |
   | `DJANGO_SUPERUSER_USERNAME` | The admin username you chose, e.g. `tienadmin` |
   | `DJANGO_SUPERUSER_EMAIL` | The admin email address |
   | `DJANGO_SUPERUSER_PASSWORD` | The strong admin password |
   | `PAYSTACK_SECRET_KEY` | **Leave empty for now** (see Step 5) |
   | `PAYSTACK_PUBLIC_KEY` | **Leave empty for now** |

   Everything else (including the secret key) is filled in automatically.
6. Click **Apply** (or **Deploy Blueprint**).
7. Render builds the site. This takes 3 to 6 minutes. You can watch progress under the service's **Events** /
   **Logs**. It is finished when you see **"Your service is live"**.
8. At the top of the service page you will see the web address, like **https://tien-ghana.onrender.com**.
   Click it: the site should open.

### Step 3: Check that it works

1. Open the web address. The home page with the 3D animation should load. (The very first visit after a quiet
   period can take up to a minute: see "Things to know" below.)
2. Go to **https://tien-ghana.onrender.com/secretariat-admin/** and log in with the admin username and password.
3. In the admin, open **Institutions**: you should see 40 institutions. Open **Programs**: you should see 9.
4. Go to the **Join** page and submit a test registration, then find it in the admin under **Student
   registrations**. Delete the test entry afterwards.
5. Open the **Donate** page: it should say **"Online giving opens soon"** with a contact form. That is expected
   until Paystack is connected.

### Step 4: Use the tienghana.org domain (optional)

1. In Render, open the **tien-ghana** service, then **Settings**, then **Custom Domains**, then **+ Add Custom Domain**.
2. Add `tienghana.org`, then add `www.tienghana.org` as well.
3. Render shows the DNS records to create (usually an **A record** for `tienghana.org` and a **CNAME** for
   `www` pointing to `tien-ghana.onrender.com`). Copy them exactly as Render shows them.
4. Log in to wherever the domain is registered and replace the old records for `@` and `www` with Render's.
   **Note:** this switches tienghana.org away from the current website. Do it when you are ready to launch.
5. Back in Render, click **Verify**. Render issues the HTTPS certificate automatically. DNS changes can take
   from a few minutes up to 48 hours.

`tienghana.org` and `www.tienghana.org` are already allowed by the site's settings; nothing else needs changing.

### Step 5: Turn on online donations (when ready)

1. Log in to **dashboard.paystack.com**. Under **Settings**, then **API Keys & Webhooks**, copy the **Test Secret Key**
   (starts with `sk_test_`) and **Test Public Key** (starts with `pk_test_`).
2. In Render: **tien-ghana** service, then **Environment**. Edit `PAYSTACK_SECRET_KEY` and `PAYSTACK_PUBLIC_KEY`,
   paste the keys and click **Save Changes**. Render restarts the site automatically.
3. In Paystack, set the **Test Webhook URL** to `https://tien-ghana.onrender.com/payments/webhook/paystack/`
   (use your own domain once Step 4 is done).
4. Make a test donation on the Donate page using one of Paystack's test cards (listed in Paystack's docs).
   The payment then appears in the admin under **Payments** with status **Success**.
5. When ready to accept real money, repeat steps 1 to 3 with the **Live** keys (`sk_live_`, `pk_live_`) and
   set the **Live Webhook URL**.

### Updating the site later

- **Content** (campuses, programs, news, events, people): log in to the admin and edit. Changes show immediately.
- **Code changes**: anything pushed to the `main` branch on GitHub is deployed automatically by Render in a
  few minutes.
- **Changing a setting or key**: Render, then **tien-ghana**, then **Environment**, then edit and **Save Changes**.
- **Changing the admin password**: use **Change password** in the admin (top right). Changing
  `DJANGO_SUPERUSER_PASSWORD` in Render does **not** change an existing account's password.

### Things to know about the free plans

- **The site sleeps when nobody visits.** On Render's free plan, the site goes to sleep after about 15 minutes
  without visitors, and the next visit takes up to a minute to wake it. After that it is fast again. For a launch
  or event, upgrade the Render service to a paid plan (Render, then **Settings**, then **Instance type**) so it never sleeps.
- **The database also pauses** when idle on Neon's free plan and wakes on the next request (a second or two).
- **Uploaded photos are not kept on the free plan.** Render's free service has no permanent disk, so photos
  uploaded in the admin (people, news, events) disappear the next time the site restarts or redeploys. Everything
  else (all text and every registration) is stored safely in Neon. Before adding photos, either upgrade
  Render and attach a disk, or ask a developer to connect free image storage such as Cloudinary.
- Check each provider's pricing page for the current free-plan limits.

### If something goes wrong

| What you see | What to do |
|---|---|
| Build fails with **"DJANGO_SUPERUSER_PASSWORD is too weak"** | Render, then **Environment**: choose a longer password, save, then **Manual Deploy**, then **Deploy latest commit**. |
| Build fails mentioning **database**, **connection** or **SSL** | Check `DATABASE_URL` is the full Neon string, starting `postgresql://` and ending `sslmode=require...`, with no spaces. |
| **Bad Request (400)** on your own domain | The domain is not in `ALLOWED_HOSTS`. Add it in Render, then **Environment**, separated by commas, and save. |
| **Forbidden (403) CSRF** when submitting a form on your own domain | Add `https://your-domain` to `CSRF_TRUSTED_ORIGINS` in Render, then **Environment**, and save. |
| Site takes a long time to open | It was asleep; wait up to a minute (see above). |
| Forgot the admin password | Ask a developer to run `python manage.py changepassword <username>` from Render, then **Shell** (paid plans), or create a new admin by changing `DJANGO_SUPERUSER_USERNAME` to a new name and redeploying. |

Render's **Logs** tab shows what the site is doing and any errors. Share a screenshot of it if you ask for help.
