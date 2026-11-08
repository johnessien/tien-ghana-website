"""Choice lists extracted from tienghana.org forms."""

INSTITUTIONS = [
    'Akatsi College of Education',
    'Academic City University College',
    'Accra Technical University',
    'Akenten Appiah-Menka University of Skills Training and Entrepreneurial Development',
    'All Nations University',
    'Ashesi University',
    'Bolgatanga Technical University',
    'Cape Coast Technical University',
    'Catholic University of Ghana',
    'CK Tedam University of Technology and Applied Sciences',
    'Dr. Hilla Limann Technical University',
    'Ghana Communication Technology University',
    'Ghana Institute of Journalism',
    'Ghana Institute of Management and Public Administration',
    'Ghana Technology University College',
    'Ho Technical University',
    'Islamic University College, Ghana',
    'Koforidua Technical University',
    'Kumasi Technical University',
    'Kwame Nkrumah University of Science and Technology',
    'Methodist University Ghana',
    'Perez University College',
    'Presbyterian University, Ghana',
    'Regional Maritime University',
    'SDA College of Education, Asokore',
    'Simon Diedong Dombo University of Business and Integrated Development Studies',
    'Sunyani Technical University',
    'Takoradi Technical University',
    'Tamale Technical University',
    'University for Development Studies',
    'University of Cape Coast',
    'University of Education, Winneba',
    'University of Environment and Sustainable Development',
    'University of Ghana',
    'University of Health and Allied Sciences',
    'University of Media, Arts and Communication',
    'University of Mines and Technology',
    'University of Professional Studies, Accra',
    'University of Energy and Natural Resources',
    'Valley View University',
]

INSTITUTION_CHOICES = [(i, i) for i in INSTITUTIONS] + [("other", "Other (type below)")]

INSTITUTION_TYPES = [
    ("university", "University"),
    ("technical_university", "Technical University"),
    ("college_of_education", "College of Education"),
    ("research_institution", "Research Institution"),
]

REGIONS = [
    ('ahafo', 'Ahafo'),
    ('ashanti', 'Ashanti'),
    ('bono', 'Bono'),
    ('bono_east', 'Bono East'),
    ('central', 'Central'),
    ('eastern', 'Eastern'),
    ('greater_accra', 'Greater Accra'),
    ('north_east', 'North East'),
    ('northern', 'Northern'),
    ('oti', 'Oti'),
    ('savannah', 'Savannah'),
    ('upper_east', 'Upper East'),
    ('upper_west', 'Upper West'),
    ('volta', 'Volta'),
    ('western', 'Western'),
    ('western_north', 'Western North'),
]

PARTNER_TYPES = [
    ("university", "University"),
    ("government", "Government Agency"),
    ("tech", "Technology Company"),
    ("corporate", "Corporate Organization"),
    ("development", "Development Partner"),
]

NEWS_CATEGORIES = [
    ("story", "Innovation Stories"),
    ("announcement", "Announcements"),
    ("project", "Student Projects"),
    ("event", "Event Coverage"),
]

DONATION_MIN, DONATION_MAX = 5, 100_000

# ---- added for the immersive front-end ----
MAP_CATEGORIES = [
    ("university", "University"),
    ("technical", "Technical university"),
    ("specialist", "Engineering, energy or health"),
    ("education", "Teacher education"),
]
ROLLOUT_WAVES = [(0, "Pilot chapter, Year 1"), (1, "Planned, Year 2"), (2, "Planned, Year 3"), (3, "Planned, Years 4 to 5")]

YEAR_OF_STUDY = [(y, y) for y in ("Year 1", "Year 2", "Year 3", "Year 4", "Postgraduate", "Recent graduate")]
MENTOR_EXPERIENCE = [(y, y) for y in ("3 to 5", "6 to 10", "11 to 20", "Over 20")]
JOIN_ROLES = [
    ("student", "Student", "Join a campus chapter"),
    ("institution", "Institution", "Host a chapter"),
    ("mentor", "Mentor", "Guide students"),
    ("ambassador", "Ambassador", "Lead on your campus"),
]
JOIN_INTERESTS = [
    "Innovation Challenges", "Innovation Fellowship", "Leadership and Excellence Forums",
    "Student Innovation Showcase", "National Collaboration Projects", "Mentorship Program",
    "Innovation Grants", "Internships and Partnerships", "Campus Ambassador",
]
CONTACT_TOPICS = [(t, t) for t in ("General question", "Partnership", "Donations", "Media", "Campus chapter", "Events")]
PARTNER_INTERESTS = [(t, t) for t in (
    "Anchor partnership", "Sector track", "Chapter partnership", "Media partnership",
    "Local content talent programme", "Commissioning a challenge", "Hiring TIEN graduates",
    "Mentors or internships in kind",
)]
DONATION_PRESETS = [50, 100, 250, 460, 4600]  # GHS
COST_PER_STUDENT = 460  # GHS: bootcamp + real project + pitch, at full scale
DESIGNATIONS = [
    ("general", "Where it is needed most"),
    ("grants", "Innovation Grants for student teams"),
    ("chapter", "A campus chapter"),
    ("media", "Tertiary Times student media"),
]
