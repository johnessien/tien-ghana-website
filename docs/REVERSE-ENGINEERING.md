# TIEN Ghana (tienghana.org): Reverse-Engineering Spec

Captured 2026-11-08. The raw mirror is in `raw/pages/` (29 pages plus CSS and logo). Screenshots are in `screenshots/`.

---

## 1. Tech stack (confirmed)

| Layer | Finding | Evidence |
|---|---|---|
| Server | nginx 1.24 on Ubuntu, HTTP→HTTPS 301, HSTS preload | Response headers |
| Backend | **Django** (server-rendered templates, trailing-slash URLs) | `/admin/` → `/admin/login/?next=/admin/`, `csrfmiddlewaretoken` on every form, `---------` empty choice in selects (Django ModelChoice/ChoiceField default) |
| CSS | **Tailwind CSS v3.4.19**, compiled to `/static/css/app.css` (43 KB), plus a page-inline `<style>` block | Banner comment in the CSS |
| Design tokens | **Material Design 3** color roles (`primary-container`, `on-surface-variant`, `secondary-fixed-dim`…) | Class names |
| Origin of design | **Google Stitch** (AI UI generator) export. Images are hot-linked from `lh3.googleusercontent.com/aida-public/…`, the Stitch asset CDN | Image URLs |
| Fonts | Google Fonts: **Epilogue** 400–900 (headlines), **Manrope** 400–800 (body), **Material Symbols Outlined** (variable icon font) | `<link>` tags |
| JS | ~25 lines of vanilla JS, with no framework | See §6 |
| Payments | **Paystack** (card, bank, MoMo) via `POST /payments/initiate/paystack/` | `/payments/` page |
| Security headers | X-Frame-Options DENY, nosniff, strict-origin-when-cross-origin, COOP same-origin. **No CSP.** | Headers |

## 2. Sitemap / routes

```
/                                   Home
/about/                             About (vision, mission, values)
  /about/vision-mission/
  /about/core-values/
  /about/leadership/                → empty state "profiles coming soon"
  /about/advisory-board/            → empty state
/programs/                          5 program cards
  /programs/innovation-challenges/  → each detail page = "Programs coming soon"
  /programs/innovation-fellowship/
  /programs/leadership-forums/
  /programs/student-showcase/
  /programs/collaboration-projects/
/opportunities/                     4 cards
  /opportunities/campus-ambassador/
  /opportunities/mentorship/        (benefits + 3-step "How it works")
  /opportunities/innovation-grants/
  /opportunities/internships/
/network/                           stats + CTA
  /network/institutions/            institution cards (UG, KNUST, Ashesi, UDS…)
  /network/community/
/partners/                          partner types + value props + EOI form
/news/?category=story|announcement|project|event   → empty "No articles yet"
/events/                            → empty "No upcoming events"
/join/                              chooser: student vs institution
  /join/register/                   Student form
  /join/register-institution/       Institution form
/contact/                           Contact info + form
/donate/                            Preset amounts + custom amount → /payments/
/payments/?amount=&description=     Paystack checkout (email only)
/payments/initiate/paystack/        POST → Paystack redirect
/admin/                             Django admin
```
`robots.txt` and `sitemap.xml` both return 404.

## 3. Inferred data model (from forms and listing pages)

| Model | Fields (✱ = required) |
|---|---|
| **StudentRegistration** | full_name✱, email✱, phone✱, institution✱ (FK / choice; 38 schools + `other`), institution_other, institution_type✱ (University · Technical University · College of Education · Research Institution), program_of_study, year_of_study, area_of_interest |
| **InstitutionRegistration** | institution_name✱, institution_other, institution_type✱, region✱ (16 Ghana regions), contact_person✱, contact_email✱, contact_phone✱, message |
| **ContactMessage** | name✱, email✱, subject✱, message✱ |
| **PartnerInquiry** | organization✱, contact_name✱, email✱, partner_type✱ (University · Government Agency · Technology Company · Corporate Organization · Development Partner), phone, message✱ |
| **Payment** | amount✱, description, email✱, reference, status (Paystack) |
| **Article** (News) | title, category ∈ {story, announcement, project, event}, … |
| **Event** | upcoming/past listing |
| **Institution** | name, short name, location (shown on /network/institutions/) |
| **Person** (Leadership / Advisory) | implied by the empty states |
| Toast messages | Django `messages` framework, `data-site-toast="true"`, auto-dismissed after 8 s |

The full institution list (38 entries) is in `raw/pages/join__register`. It is reused in `rebuild/tien/choices.py`.

## 4. Design system

### Color tokens (Material 3 roles → hex)
| Token | Hex | Use |
|---|---|---|
| primary | `#000613` | Near-black navy, footer and dark sections |
| primary-container | `#001f3f` | Brand navy: logo text, headings, buttons |
| on-primary-container | `#6f88ad` | Muted text on navy |
| primary-fixed-dim | `#afc8f0` | Light blue accents on dark |
| secondary | `#735c00` | Dark gold: link underline, hover |
| secondary-container | `#fed65b` | **Primary CTA gold** ("Join the Network") |
| secondary-fixed | `#ffe088` | Pale gold |
| secondary-fixed-dim | `#e9c349` | Gold highlight word in the hero H1 |
| on-secondary-container | `#745c00` | Text on gold |
| surface | `#f8f9fa` | Page background |
| surface-container-lowest/low/high | `#fff` / `#f3f4f5` / `#e7e8e9` | Card and section tiers |
| on-surface | `#191c1d` | Body text |
| on-surface-variant | `#43474e` | Secondary text |
| outline / outline-variant | `#74777f` / `#c4c6cf` | Borders |
| error / error-container | `#ba1a1a` / `#ffdad6` | Form errors |

**Signature background:** `.hero-gradient { background: radial-gradient(circle at top right, #001f3f 0%, #000613 100%) }`, plus large blurred glow blobs (`blur-[100–120px]`) for depth.

The palette is navy and gold. The Ghana-flag reference (gold and black star) is implied but not explicit.

### Typography
- Headlines: **Epilogue** 800/900, `tracking-tighter`. Hero H1 is roughly 72px on desktop, with one key phrase colored gold.
- Body: **Manrope** 400–600.
- Eyebrow labels: small uppercase pill chips with wide tracking (e.g. "EMPOWERING THE FUTURE").

### Shape, depth and motion
- Radii: `rounded-xl` (12px) for buttons and icons, `rounded-2xl` (16px) for cards, `rounded-[2rem]` (32px) for feature and hero media.
- Shadows: `shadow-sm` → `shadow-xl` on hover. Glassy surfaces use `bg-white/80 backdrop-blur-xl` (header) and `backdrop-blur-md` (hero stat card).
- Motion: `.reveal` fade-up (30px, 0.7s, `cubic-bezier(.4,0,.2,1)`) triggered by IntersectionObserver. Button press is `active:scale-[0.93]` and hover `scale-[0.97]`. Group hovers use `translate-x-1` on arrows, `rotate-12`/`scale-110` on icons and `scale-105` on images. `.gold-underline` animates a 2px `#735c00` bar from 0 to 100%.
- Dropdown nav: opacity, visibility and translateY(-8px→0) on `:hover`/`:focus-within`.
- Mobile menu: off-canvas `translateX(100%)` drawer, 0.35s.

### Layout
- Container: `max-w-screen-2xl mx-auto px-6 lg:px-12`.
- The header is fixed at 72px tall (the news filter bar uses `sticky top-[72px]`).
- Section rhythm: `py-20 lg:py-32`, alternating `bg-surface` and `bg-surface-container-low`.
- Home bento grid: a large "45k+ Network of Students" image tile next to smaller stat tiles (120+ hubs, 30+ partners, 16 regions).

## 5. Component inventory
1. **Header**: logo (40px rounded image + "TIEN Ghana" wordmark) · nav (Home, About▾, Programs▾, Opportunities▾, Network, Partners, Donate, News, Events) · Contact ghost link · "Join Network" navy pill.
2. **Mobile drawer** with `aria-expanded`/`aria-hidden` toggling and body scroll lock.
3. **Hero (full)**: eyebrow chip, H1 with gold span, lead text, gold primary CTA, outline secondary CTA, two tertiary text links with icons, and a media card with a floating glass stat badge.
4. **Hero (compact)**: `pt-28 pb-12`, an eyebrow or back link, then H1 and lead text. Used on inner pages.
5. **Icon feature card**: Material Symbol in a tinted square, h3, text, and an "arrow" link.
6. **Stat tile / bento tile**.
7. **Numbered step list** ("How it works" 1-2-3).
8. **Checklist card** (partners: `check_circle` bullets).
9. **Form card**: labeled inputs, `+233 XX XXX XXXX` phone placeholder, conditional "Other institution" field, full-width submit.
10. **Amount chips** (GH₵ 50/100/250/500/1000) and a custom amount form.
11. **Category filter bar** (sticky, pill links).
12. **Empty state**: icon, h3 and "check back soon".
13. **CTA band**: centered H2, two buttons.
14. **Footer**: navy, brand blurb, social icons (LinkedIn, Facebook, mail), three link columns (Explore / Network / Connect), and city list (Accra · Kumasi · Tamale).
15. **Toast** (Django messages).

## 6. Client JavaScript (complete behavior)
- IntersectionObserver (threshold 0.1) adds `.visible` to `.reveal` elements. It never unobserves.
- `toggleMobileMenu()` toggles `.open`, body `overflow-hidden` and ARIA attributes.
- `setTimeout(8000)` removes `[data-site-toast]`.

## 7. Problems found (what to improve)

### Content and credibility
- **8+ pages are empty states**: all 5 program detail pages, leadership, advisory board, news and events. The navigation promises far more than the site delivers.
- **Inconsistent stats**: the home page says "150+ Institutions", the network page says "45+ Partner Institutions", the registration form lists 38, and /network/institutions/ shows only a handful. Other figures ("45k+ students", "15k+ active", "500+ startups", "120+ hubs", "284 active projects", "95% retention") look like Stitch placeholder copy. These are a credibility risk.
- **Placeholder contact data**: `+233 (0) 500 000 000`, `partnerships@tienghana.org` (while the real address is a Gmail account), and an "Open in Maps" link to bare `https://maps.google.com`.
- The home section titled "Architectural Progress" is leftover generic copy.
- The footer has no legal or privacy page, even though the site collects personal data (phone numbers, email). Ghana's Data Protection Act 2012 (Act 843) applies.

### Technical
- **Images hot-linked from Google's Stitch CDN** (`aida-public`). These URLs can expire at any time, and they are AI stock images rather than real TIEN photos.
- `logo.jpeg` is a **1080px, 122 KB** image displayed at 40px, repeated three times. It should be an SVG or a 2× WebP.
- No `loading="lazy"`, `width`/`height` attributes or `srcset`, which causes layout shift.
- **No favicon, Open Graph/Twitter tags, canonical link, robots.txt, sitemap.xml or structured data** (`Organization`/`NGO` schema). This weakens SEO and makes social shares look poor.
- Fonts are render-blocking: there is no `preconnect`, and Epilogue loads 6 weights, Manrope 5 and Material Symbols the full variable axis (often more than 1 MB). Subsetting with `&icon_names=` would help.
- **`.reveal` content is invisible without JS** (opacity 0). It also flashes on full-page screenshots and for crawlers, and there is no `prefers-reduced-motion` handling.
- Dropdowns open on hover/focus-within only, with no keyboard Escape handling and no `aria-expanded` on desktop.
- `/payments/?amount=` accepts any amount and description from the query string. The server must validate a minimum and maximum and must not trust `description`. An "Amount 50" description ("Payment For x") is reflected back to the user. It is escaped, but it is still a phishing and social-engineering vector.
- No CSP header. No rate limiting or captcha is visible on 4 public POST forms, which invites spam.
- Admin is exposed at the default `/admin/` path.
- Phone fields are free text with no `type="tel"`, pattern or E.164 normalization.
- There is no confirmation email or double opt-in after registration.

## 8. Recommended improvements (roadmap)
1. **Real content first**: populate leadership, programs, events and news via Django admin. Hide nav items until they have content. Use one source of truth for stats, computed from the DB (e.g. `Institution.objects.count()`).
2. **Self-host media** in `/static/` or object storage, as WebP/AVIF with `srcset` and lazy loading. Replace the logo with an SVG.
3. **SEO pack**: meta and OG tags per page, `django.contrib.sitemaps`, robots.txt, JSON-LD `NGO`, favicon set.
4. **Performance**: preconnect, fewer font weights, a Material Symbols icon subset, deferred JS.
5. **Accessibility**: progressive-enhancement reveal (`html.js .reveal`), `prefers-reduced-motion`, keyboard-operable dropdowns, visible focus rings, form `aria-describedby` errors.
6. **Forms**: `type="tel"` with Ghana-number validation, honeypot plus rate limit, confirmation emails, a privacy consent checkbox, and a privacy policy page.
7. **Payments**: whitelist and clamp amounts, keep descriptions server-side, verify Paystack webhooks (HMAC-SHA512 `x-paystack-signature`), add a receipt page.
8. **Security**: CSP, move admin to a secret path or add 2FA, `SECURE_*` settings.
9. **Product features** the current site implies but lacks: a member portal (login, profile, applications), an event RSVP, program application workflows, an institution directory with a map, and a news CMS with categories.

---

## 9. Files in this package
```
REVERSE-ENGINEERING.md      ← this spec
raw/pages/                  ← full HTML mirror, app.css, logo (reference only)
screenshots/                ← desktop (1440) + mobile captures
design/tokens.css           ← CSS custom properties for all tokens
design/tailwind.config.js   ← reconstructed Tailwind theme
rebuild/tien/               ← Django app scaffold: models, forms, urls, choices, Paystack webhook
rebuild/templates/base.html ← improved accessible base layout (header/drawer/footer)
tools/                      ← outline + screenshot scripts used for this analysis
```
