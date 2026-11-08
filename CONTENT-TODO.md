# Content still needed before launch

| Item | Where it goes | Why it matters |
|---|---|---|
| Leadership names, roles, photos, bios | Admin → People (group: Leadership) | /about/leadership/ and the "Meet the team" band stay hidden until at least one exists |
| Advisory Board members | Admin → People (group: Advisory Board) | Same; hidden until filled |
| Real photos (campuses, events, students) | Event/Article covers, People photos | The site currently uses no stock photography; the 3D scene carries the visuals |
| News articles / Tertiary Times stories | Admin → Articles (set *published at*) | News stays out of the menu until something is published |
| Events (e.g. the official launch date and venue) | Admin → Events | Shown on /news/ and unlocks the News menu item |
| Confirm the 20-campus rollout and 4 pilots with each institution | Admin → Institutions (rollout wave) | The site says "to be confirmed"; pins and counts follow the data |
| Check 20 estimated coordinates | Admin → Institutions, filter *coordinates estimated* | Only the 20 rollout campuses use coordinates from the design file |
| Program details: deadlines, longer descriptions | Admin → Programs | Detail pages show the summary only |
| Data Protection Commission registration, legal review of /privacy/ | `templates/privacy.html` | Act 843 requires controllers to register; the 21-day response promise and retention periods are proposals |
| External figures on the home story (711,695 enrolment, 21.9%, Kosmos 7,000+, Ashesi 93%, Enactus 25+ years, 65% cost recovery) | `tien/content.py`, `templates/home.html` | Carried over from the design file with its sources; re-check before launch |
| Paystack live keys + webhook URL | `.env`, Paystack dashboard | Test-mode only so far |
| Social handles @tien_Ghana on Instagram and X | `templates/contact.html` | Mentioned without links; add URLs once confirmed |
