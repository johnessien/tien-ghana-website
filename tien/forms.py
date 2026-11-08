from django import forms
from django.utils.safestring import mark_safe

from . import models
from .choices import (DESIGNATIONS, DONATION_MAX, DONATION_MIN, DONATION_PRESETS, INSTITUTION_TYPES,
                      JOIN_INTERESTS, JOIN_ROLES, MENTOR_EXPERIENCE, REGIONS, YEAR_OF_STUDY)

CONSENT_LABEL = mark_safe(
    'I agree to TIEN Ghana storing and using these details to respond to me, as set out in the '
    '<a href="/privacy/">privacy policy</a>.')


def normalise_phone(value):
    p = "".join(ch for ch in value if ch.isdigit() or ch == "+")
    return "+233" + p[1:] if p.startswith("0") else p


class TienFormMixin:
    """Honeypot plus privacy consent on every form, and accessible inline errors."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["website"] = forms.CharField(
            required=False, label="Leave this field empty",
            widget=forms.TextInput(attrs={"tabindex": "-1", "autocomplete": "off"}))
        self.fields["consent_given"] = forms.BooleanField(
            required=True, label=CONSENT_LABEL,
            error_messages={"required": "Please confirm you agree to the privacy policy."})

    def clean_website(self):
        if self.cleaned_data.get("website"):
            raise forms.ValidationError("Spam detected.")
        return ""

    def full_clean(self):
        super().full_clean()
        for name in self.errors:
            if name in self.fields:
                self.fields[name].widget.attrs.update(
                    {"aria-invalid": "true", "aria-describedby": f"{self.add_prefix(name)}-err"})


class InstitutionSelect(forms.ModelChoiceField):
    """All institutions in the database, plus a 'not listed' option handled by the form."""

    def __init__(self, **kwargs):
        super().__init__(queryset=models.Institution.objects.all(), required=False,
                         empty_label="Select your institution", **kwargs)

    def to_python(self, value):
        return None if value == "other" else super().to_python(value)


# ----------------------------------------------------------------- join wizard
class JoinForm(TienFormMixin, forms.Form):
    ROLE_REQUIRED = {
        "student": ["full_name", "email", "phone", "institution", "institution_type"],
        "ambassador": ["full_name", "email", "phone", "institution", "institution_type", "motivation"],
        "institution": ["full_name", "email", "phone", "institution", "institution_type", "region"],
        "mentor": ["full_name", "email", "phone", "organisation", "expertise"],
    }
    # which wizard step each field lives on (used to reopen the right step on errors)
    STEP_OF = {"role": 0, "interests": 2, "consent_given": 3, "website": 3}

    role = forms.ChoiceField(choices=[(r[0], r[1]) for r in JOIN_ROLES], widget=forms.RadioSelect, initial="student")
    full_name = forms.CharField(label="Full name", max_length=150, required=False,
                                widget=forms.TextInput(attrs={"autocomplete": "name"}))
    email = forms.EmailField(required=False, widget=forms.EmailInput(attrs={"autocomplete": "email"}))
    phone = forms.CharField(label="Phone", max_length=20, required=False, help_text="WhatsApp preferred",
                            widget=forms.TextInput(attrs={"type": "tel", "inputmode": "tel", "autocomplete": "tel",
                                                          "placeholder": "024 123 4567"}))
    institution = InstitutionSelect(label="Institution", help_text="or pick it on the map")
    institution_other = forms.CharField(label="Institution name", max_length=200, required=False)
    institution_type = forms.ChoiceField(label="Institution type", required=False,
                                         choices=[("", "Select type")] + INSTITUTION_TYPES)
    # student
    program_of_study = forms.CharField(label="Program of study", max_length=150, required=False)
    year_of_study = forms.ChoiceField(label="Year of study", required=False,
                                      choices=[("", "Select year")] + YEAR_OF_STUDY)
    area_of_interest = forms.CharField(label="Area of interest", max_length=150, required=False,
                                       widget=forms.TextInput(attrs={"placeholder": "e.g. Renewable energy, fintech, health"}))
    # institution
    contact_role = forms.CharField(label="Your role", max_length=120, required=False,
                                   widget=forms.TextInput(attrs={"placeholder": "e.g. Dean of Students"}))
    region = forms.ChoiceField(required=False, choices=[("", "Select region")] + REGIONS)
    student_numbers = forms.IntegerField(label="Approximate student numbers", required=False, min_value=1,
                                         widget=forms.NumberInput(attrs={"inputmode": "numeric"}))
    # mentor
    organisation = forms.CharField(max_length=200, required=False,
                                   widget=forms.TextInput(attrs={"autocomplete": "organization"}))
    expertise = forms.CharField(label="Area of expertise", max_length=200, required=False,
                                widget=forms.TextInput(attrs={"placeholder": "e.g. Mining engineering"}))
    years_experience = forms.ChoiceField(label="Years of experience", required=False, choices=MENTOR_EXPERIENCE)
    # ambassador
    motivation = forms.CharField(label="Why would you lead TIEN on your campus?", required=False,
                                 widget=forms.Textarea(attrs={"rows": 4}))
    interests = forms.MultipleChoiceField(required=False, choices=[(i, i) for i in JOIN_INTERESTS],
                                          widget=forms.CheckboxSelectMultiple)

    def clean_phone(self):
        return normalise_phone(self.cleaned_data.get("phone", ""))

    def clean(self):
        data = super().clean()
        role = data.get("role")
        if not role:
            return data
        for name in self.ROLE_REQUIRED[role]:
            if name == "institution":
                if not data.get("institution") and not data.get("institution_other"):
                    self.add_error("institution", "Select your institution, or choose “not listed” and type its name.")
            elif not data.get(name) and name not in self.errors:
                self.add_error(name, "This field is required.")
        if data.get("phone"):
            try:
                models.phone_validator(data["phone"])
            except forms.ValidationError as e:
                self.add_error("phone", e)
        if role == "student" and data.get("email") and \
                models.StudentRegistration.objects.filter(email__iexact=data["email"]).exists():
            self.add_error("email", "This email is already registered. Contact us if you need to update your details.")
        return data

    @property
    def first_error_step(self):
        if not self.errors:
            return None
        return min(self.STEP_OF.get(name, 1) for name in self.errors)

    def save(self):
        d, role = self.cleaned_data, self.cleaned_data["role"]
        inst = {"institution": d.get("institution"),
                "institution_other": "" if d.get("institution") else d.get("institution_other", "")}
        common = {"consent_given": True, "interests": d.get("interests", [])}
        if role == "student":
            return models.StudentRegistration.objects.create(
                full_name=d["full_name"], email=d["email"].lower(), phone=d["phone"],
                institution_type=d["institution_type"], program_of_study=d.get("program_of_study", ""),
                year_of_study=d.get("year_of_study", ""), area_of_interest=d.get("area_of_interest", ""),
                **inst, **common)
        if role == "institution":
            return models.InstitutionRegistration.objects.create(
                contact_person=d["full_name"], contact_email=d["email"].lower(), contact_phone=d["phone"],
                contact_role=d.get("contact_role", ""), institution_type=d["institution_type"],
                region=d["region"], student_numbers=d.get("student_numbers"), **inst, **common)
        slug = "mentorship" if role == "mentor" else "campus-ambassador"
        return models.Application.objects.create(
            program=models.Program.objects.get(slug=slug), role=role, full_name=d["full_name"],
            email=d["email"].lower(), phone=d["phone"], organisation=d.get("organisation", ""),
            expertise=d.get("expertise", ""), years_experience=d.get("years_experience", "") if role == "mentor" else "",
            motivation=d.get("motivation", ""), **(inst if role == "ambassador" else {}), **common)


# ----------------------------------------------------------------- simple forms
class ContactForm(TienFormMixin, forms.ModelForm):
    class Meta:
        model = models.ContactMessage
        fields = ["name", "email", "topic", "message", "consent_given"]
        widgets = {"name": forms.TextInput(attrs={"autocomplete": "name"}),
                   "email": forms.EmailInput(attrs={"autocomplete": "email"})}


class PartnerInquiryForm(TienFormMixin, forms.ModelForm):
    class Meta:
        model = models.PartnerInquiry
        fields = ["contact_name", "organization", "email", "phone", "interest", "message", "consent_given"]
        widgets = {"contact_name": forms.TextInput(attrs={"autocomplete": "name"}),
                   "organization": forms.TextInput(attrs={"autocomplete": "organization"}),
                   "email": forms.EmailInput(attrs={"autocomplete": "email"}),
                   "phone": forms.TextInput(attrs={"type": "tel", "autocomplete": "tel"})}

    def clean_phone(self):
        return normalise_phone(self.cleaned_data.get("phone", ""))


class SubscribeForm(TienFormMixin, forms.ModelForm):
    class Meta:
        model = models.Subscriber
        fields = ["email", "consent_given"]
        widgets = {"email": forms.EmailInput(attrs={"placeholder": "you@example.com", "autocomplete": "email"})}
        error_messages = {"email": {"unique": "You're already subscribed. Thank you!"}}

    def clean_email(self):
        return self.cleaned_data["email"].lower()


# ----------------------------------------------------------------- donate
class DonationForm(TienFormMixin, forms.Form):
    preset = forms.ChoiceField(
        label="Amount", initial="460", widget=forms.RadioSelect,
        choices=[(str(a), f"GHS {a:,}") for a in DONATION_PRESETS] + [("other", "Other")])
    custom = forms.DecimalField(label="Your amount (GHS)", required=False, min_value=DONATION_MIN,
                                max_value=DONATION_MAX, decimal_places=2,
                                widget=forms.NumberInput(attrs={"inputmode": "decimal", "placeholder": "e.g. 1000", "step": "1"}))
    designation = forms.ChoiceField(label="Direct my gift to", choices=DESIGNATIONS, initial="general")
    campus = forms.ModelChoiceField(label="Which campus?", required=False, empty_label="Select a campus",
                                    queryset=models.Institution.objects.in_network())
    email = forms.EmailField(label="Email for your receipt", widget=forms.EmailInput(attrs={"autocomplete": "email"}))

    def clean(self):
        d = super().clean()
        if d.get("preset") == "other":
            if d.get("custom") is None and "custom" not in self.errors:
                self.add_error("custom", f"Enter an amount between GHS {DONATION_MIN} and GHS {DONATION_MAX:,}.")
            d["amount"] = d.get("custom")
        elif d.get("preset"):
            d["amount"] = int(d["preset"])
        if d.get("designation") == "chapter" and not d.get("campus"):
            self.add_error("campus", "Choose the campus chapter your gift should support.")
        return d
