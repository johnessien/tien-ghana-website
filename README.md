# TIEN Ghana: Django site with the immersive front-end

Deploying: follow **HANDOVER.md → Deploy on Render and Neon** (free Render web service + free Neon PostgreSQL,
auto-deployed from GitHub via `render.yaml` and `build.sh`).

## Run locally
```bash
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # set DJANGO_DEBUG=1; leave DATABASE_URL empty for SQLite
python manage.py migrate      # also seeds 40 institutions (with coordinates) and 9 programs/opportunities
python manage.py createsuperuser
python manage.py runserver    # admin is at /secretariat-admin/ (ADMIN_PATH)
python manage.py test tien    # every form, Paystack (mocked), webhook signature, stats, menu, deploy commands
python manage.py paystack_smoke          # live Paystack TEST transaction (needs sk_test_ key), prints checkout URL
python manage.py paystack_smoke --verify TIEN-SMOKE-xxxx
```

## Production
| Piece | How |
|---|---|
| Server | `gunicorn config.wsgi:application` (start command in `render.yaml`) |
| Database | `DATABASE_URL` via dj-database-url, `sslmode=require`; Neon's pooled endpoint auto-disables server-side cursors |
| Static files | whitenoise, compressed + hashed (`collectstatic` in `build.sh`) |
| Admin account | `python manage.py ensure_superuser` reads `DJANGO_SUPERUSER_*`, creates it once, never overwrites |
| Admin roles | Superusers = full control. Staff in the **Submissions reviewers** group (created/topped up on every `migrate`, `tien/roles.py`) read submissions and update only handled/approved/status; no delete, no CSV, no payments/content/users |
| Health check | `/healthz` (answers before host check/HTTPS redirect; 503 if the database is down) |
| Security | `DEBUG` off by default; `SECRET_KEY` required; HTTPS redirect, HSTS (1 year, preload), secure cookies |
| Paystack off | Empty `PAYSTACK_SECRET_KEY` makes `/donate/` show "Online giving opens soon" with a contact form |
| Uploads | `MEDIA_ROOT` is local disk: **not persistent on Render's free plan** (see HANDOVER.md) |

## Front-end layout
| File | What it is |
|---|---|
| `templates/base.html` | `<head>` (SEO, OG, JSON-LD, fonts, no-JS guard), header + mega menu, mobile drawer, page wipe, fixed WebGL canvas, toasts, footer, scripts |
| `templates/*.html` | One real page per old hash route: home, about, programs, opportunities, network, partners, donate, join, contact, news; plus privacy, program detail, people, news/event detail, receipt |
| `static/css/site.css` | The immersive design system + form/toast/no-JS additions |
| `static/js/world.js` | Three.js particle world, SCENE table, wipe, menu, home story, network map, donate gauge, join wizard |

`<body data-page="…">` selects the 3D state from `SCENE` in `world.js`. The home page alone renders the 8-chapter
scroll story. Campus pins and wave counts come from the database via `{{ world|json_script }}`.

## How the data flows
- **Statistics**: `views.site_stats()` (campus count, pilots, cumulative wave counts 4 → 8 → 12 → 20, regions). Change
  `Institution.rollout_wave` / `is_member` in admin and every page and the 3D map update.
- **Map**: institutions with a rollout wave or `is_member=True` appear on /network/ and as 3D pins. Pilot = wave 0.
- **Menu**: News, Leadership and Advisory Board appear only once they have content (`context_processors.py`).
- **Forms → models**: Join wizard → `StudentRegistration` / `InstitutionRegistration` / `Application` (mentorship or
  campus-ambassador); Contact → `ContactMessage`; Partner → `PartnerInquiry`; Subscribe → `Subscriber`;
  Donate → `Payment` + Paystack initialise (server-side; the amount is never in a URL). All forms have a honeypot and a
  required privacy-consent checkbox; errors render inline with `aria-invalid`/`aria-describedby`.
- **Payments**: `/donate/` POST → Paystack initialise → checkout → `/payments/callback/` verifies amount + currency →
  receipt. Set the webhook URL in the Paystack dashboard to `https://<domain>/payments/webhook/paystack/` (HMAC-SHA512 checked).

Old tienghana.org URLs (`/join/register/`, `/network/institutions/`, `/payments/`, …) 301 to their new homes.
