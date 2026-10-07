"""Remplit une base de DÉVELOPPEMENT avec des données fictives (jamais en production).

    python manage.py seed_demo

Crée notamment :
- admin@magellans.test (super-utilisateur, présidence + trésorerie + magasin) ;
- membre@magellans.test (adhérent·e à jour) ;
- du matériel, des réservations dans tous les états, des notes de frais, des
  opérations, des projets, des ressources et une demande d'aide.
Mot de passe de tous les comptes : « magellans-demo ».
"""

import datetime
import random
from decimal import Decimal

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from PIL import Image, ImageDraw

from bank.models import Expense, Invoice, Operation
from dashboard.models import Project, ProjectFundingRequest, ResourceFile, RoleMap
from members.models import Member, Person
from memberships.models import Membership, Season
from warehouse.models import Contract, Item, Order, OrderLine, OrderStatus, Tag

PASSWORD = "magellans-demo"


def _image(color, size=(600, 450), label=""):
    img = Image.new("RGB", size, color)
    draw = ImageDraw.Draw(img)
    draw.ellipse((size[0] * 0.3, size[1] * 0.2, size[0] * 0.7, size[1] * 0.8), outline="white", width=8)
    if label:
        draw.text((20, 20), label, fill="white")
    from io import BytesIO

    buffer = BytesIO()
    img.save(buffer, "WEBP", quality=80)
    return ContentFile(buffer.getvalue(), name=f"{label or 'demo'}.webp")


class Command(BaseCommand):
    help = "Données fictives pour le développement (refusé si DEBUG est désactivé)."

    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError("seed_demo est réservé au développement (DEBUG=1).")
        random.seed(42)
        now = timezone.now()
        season = Season.current()

        def account(email, first, last, roles=(), superuser=False):
            user = Member.objects.filter(email=email).first()
            if user is None:
                person = Person(first_name=first, last_name=last, email=email, phone="0612345678", role="E")
                if superuser:
                    user = Member.objects.create_superuser(email, PASSWORD, person=person)
                else:
                    user = Member.objects.create_user(email, PASSWORD, person=person)
            person = user.person
            person.board_roles = list(roles)
            person.phone = person.phone or "0612345678"
            person.save()
            return user

        admin = account("admin@magellans.test", "Camille", "Admin", roles=["P", "T", "G"], superuser=True)
        member = account("membre@magellans.test", "Lou", "Membre")
        account("tresorerie@magellans.test", "Sacha", "Trésorier", roles=["T"])
        account("magasin@magellans.test", "Alex", "Magasin", roles=["G"])
        account("communication@magellans.test", "Noa", "Communication", roles=["C"])
        if season:
            for user in (admin, member):
                Membership.objects.get_or_create(
                    person=user.person, season=season, defaults={"source": "manual", "amount": Decimal("5.00"), "payment_method": "cash"}
                )

        tags = {}
        for name, color in [("Caméra", "#e08700"), ("Son", "#0ea5e9"), ("Lumière", "#ef4444"), ("Machinerie", "#22c55e"), ("Accessoires", "#8b5cf6")]:
            tags[name], _ = Tag.objects.get_or_create(name=name, defaults={"color": color})
        catalogue = [
            ("Caméra Sony FX3", "Caméra", 1, 5), ("Blackmagic Pocket 6K", "Caméra", 2, 4), ("Micro canon Rode NTG3", "Son", 2, 4),
            ("Enregistreur Zoom F6", "Son", 1, 5), ("Perche 3 m", "Son", 3, 3), ("Projecteur Aputure 300d", "Lumière", 2, 4),
            ("Panneau LED Nanlite", "Lumière", 4, 3), ("Réflecteur 5-en-1", "Lumière", 2, 2), ("Trépied vidéo Sachtler", "Machinerie", 3, 4),
            ("Slider 80 cm", "Machinerie", 1, 3), ("Batterie NP-F970", "Accessoires", 8, 4), ("Moniteur 7 pouces", "Accessoires", 2, 5),
        ]
        items = []
        palette = ["#7f3f17", "#b96204", "#14100d", "#4a3f36", "#985025"]
        for index, (name, tag, stock, state) in enumerate(catalogue):
            item, created = Item.objects.get_or_create(
                name=name, defaults={"max_stock": stock, "state": state, "availability": 1, "description": f"{name} : matériel de démonstration."}
            )
            if created:
                item.tags.add(tags[tag])
                item.image.save(f"objet-{item.pk}.webp", _image(palette[index % len(palette)], (500, 500), name[:12]), save=True)
            items.append(item)

        def order(status, start_in_days, days, user=member, lines=2, project="Court-métrage « Le Phare »"):
            start = now + datetime.timedelta(days=start_in_days)
            o = Order.objects.create(
                user=user,
                status=status,
                date_start=start.replace(hour=18, minute=0, second=0, microsecond=0),
                date_end=(start + datetime.timedelta(days=days)).replace(hour=10, minute=0, second=0, microsecond=0),
                project_name=project,
                message="Tournage en extérieur, merci !",
                quantities="{}",
            )
            for item in random.sample(items, lines):
                OrderLine.objects.create(order=o, item=item, quantity=1)
            return o

        if not Order.objects.exclude(status=OrderStatus.DRAFT).exists():
            order(OrderStatus.PENDING, 5, 3)
            order(OrderStatus.PENDING, 12, 2, user=admin, project="Clip « Néons »")
            accepted = order(OrderStatus.ACCEPTED, 3, 2, lines=3)
            Contract.objects.create(
                order=accepted, director_name="Lou Membre", director_phone="0612345678", director_email="membre@magellans.test",
                production_name="Prod indépendante", production_phone="0612345678", production_email="prod@example.org",
            )
            order(OrderStatus.SIGNED, -1, 4, lines=2, project="Documentaire « Montreuil »")
            order(OrderStatus.RETURNED, -20, 3)
            order(OrderStatus.REFUSED, -10, 2)

        projects = []
        for name, genre, public in [("Le Phare", "Fiction", True), ("Néons", "Clip", True), ("Montreuil, la nuit", "Documentaire", False)]:
            project, created = Project.objects.get_or_create(
                name=name,
                defaults={
                    "genre": genre,
                    "desc": "Un projet de démonstration, tourné par les membres de l'association.",
                    "short_desc": "Une histoire de lumière et de rencontres.",
                    "public": public,
                    "release_date": timezone.localdate() - datetime.timedelta(days=random.randint(30, 600)),
                    "director": member.person,
                    "video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ" if name == "Le Phare" else "",
                },
            )
            if created:
                project.poster.save(f"{project.slug}.webp", _image(palette[len(projects) % len(palette)], (600, 900), name), save=True)
                RoleMap.objects.get_or_create(person=member.person, project=project, role_name=1)
                RoleMap.objects.get_or_create(person=admin.person, project=project, role_name=4)
            projects.append(project)

        if not Invoice.objects.exists():
            invoice = Invoice.objects.create(title="Régie tournage « Le Phare »", project=projects[0], author=member, role="Régie", status="V", comm="Courses et transport.")
            Expense.objects.create(title="Courses régie", date=timezone.localdate(), amount=42.5, author=member, linked_invoice=invoice, proof=ContentFile(b"%PDF-1.4 demo", name="ticket.pdf"))
            Expense.objects.create(title="Essence", date=timezone.localdate(), amount=31.2, author=member, linked_invoice=invoice)
            invoice.refresh_total()

        if not Operation.objects.exists():
            for desc, kind, amount, days in [
                ("Adhésions septembre (HelloAsso)", "C", 160, 30), ("Achat micro canon", "D", 289.9, 25),
                ("Subvention municipale", "C", 800, 60), ("Frais bancaires", "D", 12, 15), ("Remboursement note de frais", "R", 73.7, 5),
            ]:
                Operation.objects.create(desc=desc, type=kind, amount=amount, third_party=admin.person, date=timezone.localdate() - datetime.timedelta(days=days))

        if not ProjectFundingRequest.objects.exists():
            ProjectFundingRequest.objects.create(
                name="Le Phare", asker=member, role="Réalisation", directors="Lou Membre", genre="Fiction", duration=12,
                production="Autoproduction", previsional_shoot_start_date=timezone.localdate() + datetime.timedelta(days=40),
                previsional_shoot_end_date=timezone.localdate() + datetime.timedelta(days=43), explanation="Location d'un véhicule et décors.",
                funding_value=400, script=ContentFile(b"%PDF-1.4 demo", name="scenario.pdf"), intention_note=ContentFile(b"%PDF-1.4 demo", name="note.pdf"),
                previsional_budget_plan=ContentFile(b"%PDF-1.4 demo", name="budget.pdf"), contact_list=ContentFile(b"%PDF-1.4 demo", name="contacts.pdf"),
            )

        if not ResourceFile.objects.exists():
            ResourceFile.objects.create(name="Modèle de feuille de service", category="Production", desc="À dupliquer pour chaque journée de tournage.", associated_file=ContentFile(b"%PDF-1.4 demo", name="feuille-de-service.pdf"))
            ResourceFile.objects.create(name="Guide du magasin", category="Magasin", external_url="https://example.org/guide")

        self.stdout.write(self.style.SUCCESS(f"Données de démonstration prêtes. Comptes : admin@magellans.test / membre@magellans.test — mot de passe « {PASSWORD} »."))
