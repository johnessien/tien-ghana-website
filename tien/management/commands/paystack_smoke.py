"""Live Paystack TEST-mode check: python manage.py paystack_smoke [--amount 460]

Initialises a real test transaction with the keys in .env, prints the checkout URL to pay with a
Paystack test card or test mobile money number, then (with --verify REF) confirms it via the API."""
import secrets

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from tien.views import paystack_request


class Command(BaseCommand):
    help = "Initialise (or --verify) a Paystack test-mode transaction using the keys in .env"

    def add_arguments(self, parser):
        parser.add_argument("--amount", type=int, default=460, help="GHS")
        parser.add_argument("--email", default="test-donor@example.com")
        parser.add_argument("--verify", metavar="REFERENCE")

    def handle(self, amount, email, verify, **_):
        key = settings.PAYSTACK_SECRET_KEY
        if not key:
            raise CommandError("PAYSTACK_SECRET_KEY is not set. Copy .env.example to .env and add your sk_test_ key.")
        if not key.startswith("sk_test_"):
            raise CommandError("Refusing to run: this command only uses TEST keys (sk_test_...).")
        if verify:
            d = paystack_request("GET", f"/transaction/verify/{verify}").json()
            self.stdout.write(f"{verify}: status={d.get('data', {}).get('status')} amount={d.get('data', {}).get('amount')} "
                              f"currency={d.get('data', {}).get('currency')} message={d.get('message')}")
            return
        ref = f"TIEN-SMOKE-{secrets.token_hex(4)}"
        r = paystack_request("POST", "/transaction/initialize",
                             json={"email": email, "amount": amount * 100, "currency": "GHS", "reference": ref})
        body = r.json()
        if not body.get("status"):
            raise CommandError(f"Paystack rejected the request ({r.status_code}): {body.get('message')}")
        self.stdout.write(self.style.SUCCESS(f"Initialised {ref} for GHS {amount}"))
        self.stdout.write(f"Pay here with a Paystack test card: {body['data']['authorization_url']}")
        self.stdout.write(f"Then run: python manage.py paystack_smoke --verify {ref}")
