"""Editorial copy carried over from the immersive front-end. Data that changes
(campuses, programs, stats, news, people) lives in the database instead."""

ICONS = {
    "bulb": '<path d="M9 18h6M10 21h4M12 3a6 6 0 0 0-3.5 10.9c.6.5 1 1.2 1 2.1h5c0-.9.4-1.6 1-2.1A6 6 0 0 0 12 3z"/>',
    "star": '<path d="M12 3l2.7 5.6 6.1.9-4.4 4.3 1 6.1L12 17l-5.4 2.9 1-6.1L3.2 9.5l6.1-.9z"/>',
    "chat": '<path d="M4 5h16v10H9l-5 4z"/>',
    "flask": '<path d="M9 3h6M10 3v6l-5 9a2 2 0 0 0 1.7 3h10.6a2 2 0 0 0 1.7-3l-5-9V3"/>',
    "hub": '<circle cx="12" cy="12" r="3"/><path d="M12 2v4M12 18v4M2 12h4M18 12h4M5 5l3 3M16 16l3 3M19 5l-3 3M8 16l-3 3"/>',
    "mega": '<path d="M3 11v2a1 1 0 0 0 1 1h2l5 4V6L6 10H4a1 1 0 0 0-1 1zM16 8a5 5 0 0 1 0 8"/>',
    "mentor": '<circle cx="9" cy="8" r="3.5"/><path d="M3 20c0-3.3 2.7-6 6-6s6 2.7 6 6M17 11l2 2 3-4"/>',
    "coin": '<rect x="3" y="6" width="18" height="12" rx="2"/><circle cx="12" cy="12" r="2.5"/>',
    "brief": '<path d="M4 8h16v11H4zM9 8V5h6v3"/>',
}

VALUES = [
    ("Practical first", "Every program ends in something built, pitched, placed or published."),
    ("Every campus counts", "Technical, engineering, health, agriculture and teacher-training campuses get the same access as the big universities."),
    ("Industry in the room", "Employers co-design challenges, mentor and hire."),
    ("Measured honestly", "We publish what worked and what did not."),
    ("Student-led, professionally run", "Chapters are led by students and backed by a small professional secretariat."),
]

GOVERNANCE = [
    ("Board of Directors", "Approves budget, work plan and audited accounts; monitors results and risk."),
    ("Advisory Board", "Industry, academic and alumni advisers who open doors and review quality."),
    ("Secretariat", "A small professional team running programmes, media, partnerships and finance."),
    ("Campus chapters", "Student presidents and core teams, guided by a faculty or alumni adviser."),
]

TIERS = [
    ("Anchor Partner", "Names the national Innovation Challenge, with an Advisory Board seat and first pick of interns.", True),
    ("Sector Track Partner", "Owns one industry track: sets two real problems a year, judges the finals and recruits.", False),
    ("Chapter Partner", "Trains 100 students on a named campus, with a quarterly chapter report.", False),
    ("Media Partner", "Reaches every TIEN campus through Tertiary Times features and campaigns.", False),
]

SERVICES = [
    ("Local content talent programmes", "We design and run graduate-trainee pipelines for mining and energy companies that must train and recruit Ghanaians."),
    ("Commission a challenge", "Set one real problem and receive tested solutions from student teams across the network."),
    ("Hire TIEN graduates", "Project-tested interns and graduates, matched to your roles."),
]

ACCOUNTABILITY = [
    ("Quarterly scorecard", "Reach, skills gained, projects, placements and spend."),
    ("Two go/no-go gates", "No phase is funded until the one before it has delivered."),
    ("Audited accounts", "An annual audit and a public impact report every September."),
    ("Protected funds", "Restricted money is tracked to its purpose, with cash held in reserve."),
    ("Non-partisan", "TIEN serves students on every campus and carries no party branding."),
]

TRACKS = ["Mining and minerals", "Oil and gas", "Energy", "Construction and built environment",
          "Agriculture and food", "Health", "Finance", "Digital"]

# Home story: national figures are external and sourced on the page itself.
NATIONAL = {
    "enrolment": 711695,
    "youth_unemployment": "21.9%",
    "sources": "Sources: GTEC 2022/2023 via Ghana News Agency; Ghana Statistical Service, 2025",
}
CHAPTER_TITLES = ["Welcome", "The pressure", "The trap", "The network", "The journey", "The proof", "Sustainability", "Join us"]
