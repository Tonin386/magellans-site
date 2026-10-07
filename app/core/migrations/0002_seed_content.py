"""Contenus initiaux : reprise des textes et images de l'ancienne page d'accueil.

Tout est ensuite modifiable par le CA depuis l'espace CA (« Contenus du site »).
"""

import logging
from pathlib import Path

from django.core.files.base import ContentFile
from django.core.files.storage import storages
from django.db import migrations

logger = logging.getLogger(__name__)
SEED_DIR = Path(__file__).resolve().parent.parent / "seed"

TEAM_2025 = [
    {
        "name": "Sarah Duvallet",
        "role_title": "Présidente",
        "email": "sarah.duvallet@magellans.fr",
        "instagram_url": "https://www.instagram.com/sarah.dvlt/",
        "linkedin_url": "https://www.linkedin.com/in/sarah-duvallet-68576b184/",
        "photo": "team/sarah_duvallet.webp",
    },
    {
        "name": "Pénélope Tricart",
        "role_title": "Trésorière",
        "email": "penelope.tricart@magellans.fr",
        "instagram_url": "https://www.instagram.com/penetrct/",
        "linkedin_url": "https://www.linkedin.com/in/penelopetricart/",
        "photo": "team/penelope_tricart.webp",
    },
    {
        "name": "Axelle Servat",
        "role_title": "Secrétaire et magasinière",
        "email": "axelle.servat@magellans.fr",
        "instagram_url": "https://www.instagram.com/axelleservat/",
        "linkedin_url": "https://www.linkedin.com/in/axelle-servat-441453165/",
        "photo": "team/axelle_servat.webp",
    },
]

TIMELINE = [
    ("Septembre 2020", "Création de Magellans",
     "Magellans devient officiellement une association loi 1901. Première projection d'un projet. Premières adhésions enregistrées.",
     "timeline/2020-creation.webp"),
    ("Octobre 2020", "48 Hour Film Project",
     "Magellans participe à son premier 48 Hour Film Project. Un rendez-vous maintenant annuel pour tous les membres.",
     "timeline/2020-48hfp.webp"),
    ("Début 2021", "Ouverture du magasin",
     "Le magasin de Magellans ouvre ses portes. Les membres ont désormais accès à du matériel gratuitement !",
     "timeline/2021-magasin.webp"),
    ("Mai 2022", "Émission Le Goûter",
     "Le Goûter est le premier projet aidé financièrement par Magellans : une émission retransmise en direct sur Twitch.",
     "timeline/2022-le-gouter.webp"),
    ("Avril 2024", "Nouveau site internet",
     "Le site officiel de Magellans est en ligne : réservation de matériel, demandes d'aide, notes de frais et bien plus encore.",
     "timeline/2024-site.webp"),
    ("Octobre 2026", "Le site fait peau neuve",
     "Adhésions synchronisées avec HelloAsso, réservations avec disponibilités en temps réel, contrats signés en ligne et un espace dédié au CA.",
     "timeline/2026-refonte.webp"),
]

SERVICES = [
    ("users", "Développe ton réseau",
     "Rencontre d'autres personnes qui aiment le cinéma et l'audiovisuel, sur les tournages comme autour d'un verre."),
    ("send", "Propose ton projet",
     "Un soutien humain et financier pour tes projets personnels ou professionnels."),
    ("package", "Emprunte du matériel",
     "Caméras, son, lumière… le matériel du magasin est prêté gratuitement à tous les membres."),
    ("clapperboard", "Captations",
     "Captations de spectacles et d'évènements de tout genre, partout en France."),
]

FAQ = [
    ("membership", "Combien coûte l'adhésion ?",
     "Le montant de la cotisation est indiqué sur la page d'adhésion (5 € pour la saison 2026-2027). Elle couvre "
     "toute la saison, de septembre à fin août. Tu peux y ajouter un don pour soutenir les projets de l'association."),
    ("membership", "Comment adhérer ?",
     "Directement en ligne via HelloAsso, depuis la page « Adhérer ». Le paiement est sécurisé et ton adhésion est "
     "enregistrée automatiquement sur le site : tu reçois ensuite un e-mail pour accéder à ton espace membre."),
    ("membership", "J'ai adhéré mais je n'ai rien reçu, que faire ?",
     "Vérifie tes courriers indésirables. L'adhésion est associée à l'adresse e-mail saisie dans le formulaire "
     "HelloAsso (champ « Adresse mail »). Si le problème persiste, écris-nous : nous vérifierons ton adhésion."),
    ("membership", "Je n'ai pas de carte bancaire, puis-je adhérer ?",
     "Oui : contacte un membre du CA, l'adhésion peut être réglée autrement puis enregistrée à la main."),
    ("warehouse", "Qui peut emprunter du matériel ?",
     "Les membres inscrits sur le site, avec un profil complet. Le prêt est gratuit ; un contrat de prêt est à "
     "signer en ligne une fois la réservation acceptée."),
    ("warehouse", "Comment se passe le retrait du matériel ?",
     "Une fois ta réservation acceptée et le contrat signé, le magasin te donne rendez-vous pour le retrait et le "
     "retour du matériel aux dates prévues."),
]

PAGES = [
    ("mentions-legales", "Mentions légales", """
## Éditeur du site

Le site **magellans.fr** est édité par l'association **Magellans**, association loi 1901 enregistrée sous le numéro RNA **W931023484**, dont le siège est situé rue du Colonel Delorme, 93100 Montreuil.

Contact : [contact@magellans.fr](mailto:contact@magellans.fr)

**Directeur·ice de la publication :** le ou la président·e de l'association.

## Hébergement

Le site est hébergé sur un serveur privé virtuel loué par l'association auprès de la société OVH SAS, 2 rue Kellermann, 59100 Roubaix, France.

## Propriété intellectuelle

Les contenus du site (textes, logos, affiches, photos, vidéos) appartiennent à l'association Magellans ou à leurs auteur·ices respectif·ves. Toute reproduction sans autorisation est interdite.

## Paiements

Les adhésions et les dons sont encaissés par la plateforme **HelloAsso**. Aucune donnée bancaire n'est traitée ni conservée par le site magellans.fr.
"""),
    ("confidentialite", "Politique de confidentialité", """
L'association Magellans attache une grande importance à la protection de tes données personnelles. Cette page explique quelles données nous collectons, pourquoi et combien de temps nous les conservons.

## Responsable du traitement

Association Magellans, rue du Colonel Delorme, 93100 Montreuil — [contact@magellans.fr](mailto:contact@magellans.fr).

## Données collectées et finalités

| Données | Finalité | Base légale |
|---|---|---|
| Nom, prénom, e-mail, téléphone | Gestion des adhésions et de ton compte | Exécution du contrat d'adhésion |
| Réservations de matériel, contrats de prêt | Gestion du prêt de matériel | Exécution du contrat de prêt |
| Notes de frais et justificatifs | Remboursement des frais engagés | Obligation comptable |
| Demandes d'aide à projet et documents joints | Étude des demandes par le CA | Mesures précontractuelles |
| Messages du formulaire de contact | Réponse à ta demande | Intérêt légitime |
| Mesure d'audience (Google Analytics) | Statistiques de fréquentation | **Consentement** (bandeau cookies) |

Les paiements sont traités par **HelloAsso** : nous ne recevons jamais tes coordonnées bancaires.

## Destinataires

Les données sont accessibles uniquement aux membres du conseil d'administration, dans la limite de leurs fonctions (par exemple, les justificatifs de dépenses sont réservés à la trésorerie). Elles ne sont jamais vendues ni cédées.

## Durées de conservation

- Compte du site : tant que le compte est actif, puis 3 ans après la dernière activité.
- Adhésions, notes de frais et opérations comptables : 10 ans (obligations comptables).
- Messages du formulaire de contact : 1 an.

## Tes droits

Tu disposes d'un droit d'accès, de rectification, d'effacement, de limitation, d'opposition et de portabilité de tes données. Pour l'exercer, écris à [contact@magellans.fr](mailto:contact@magellans.fr). Tu peux également introduire une réclamation auprès de la CNIL ([cnil.fr](https://www.cnil.fr)).

## Cookies

Le site utilise un cookie de session (connexion) et un cookie de sécurité (protection des formulaires), indispensables à son fonctionnement. Les cookies de mesure d'audience ne sont déposés qu'avec ton accord, que tu peux retirer à tout moment depuis le lien « Gérer les cookies » en bas de page.
"""),
    ("cgu-magasin", "Conditions d'utilisation du magasin", """
Le magasin de Magellans prête gratuitement du matériel audiovisuel aux membres de l'association.

## Qui peut réserver ?

Toute personne disposant d'un compte sur le site, dont le profil est complet. Le conseil d'administration peut réserver le magasin aux adhérent·es à jour de cotisation.

## Déroulement d'une réservation

1. Choisis tes dates et le matériel souhaité, puis envoie ta demande.
2. L'équipe du magasin étudie la demande et peut l'accepter, l'accepter avec modifications ou la refuser.
3. Une fois la demande acceptée, tu signes le **contrat de prêt** en ligne.
4. Le matériel est retiré puis rendu aux dates convenues, à l'adresse indiquée.

## Engagements de l'emprunteur·se

L'emprunteur·se est responsable du matériel pendant toute la durée du prêt, s'engage à l'utiliser conformément à sa notice, à le sécuriser contre le vol, à signaler sans délai tout dommage et à le rendre à la date prévue. Le détail des engagements figure dans le contrat de prêt.

## Annulation

Tu peux annuler ta demande depuis ton espace membre tant que le matériel n'a pas été retiré. Merci de prévenir le plus tôt possible.
"""),
]


def _copy(storage_alias, source, target):
    try:
        path = SEED_DIR / source
        if not path.exists():
            return ""
        storage = storages[storage_alias]
        if storage.exists(target):
            return target
        return storage.save(target, ContentFile(path.read_bytes()))
    except Exception:  # un problème de fichier ne doit jamais bloquer la migration
        logger.exception("Impossible de copier %s", source)
        return ""


def forwards(apps, schema_editor):
    SiteSettings = apps.get_model("core", "SiteSettings")
    TeamMember = apps.get_model("core", "TeamMember")
    TimelineEntry = apps.get_model("core", "TimelineEntry")
    Service = apps.get_model("core", "Service")
    Page = apps.get_model("core", "Page")
    FAQEntry = apps.get_model("core", "FAQEntry")
    Season = apps.get_model("memberships", "Season")

    settings_obj, created = SiteSettings.objects.get_or_create(pk=1)
    if created and not settings_obj.contract_signature:
        settings_obj.contract_signature = _copy(
            "private", "private/signature-magasin.jpeg", "site/signature/signature-magasin.jpeg"
        )
        settings_obj.save()

    if not TeamMember.objects.exists():
        season = Season.objects.filter(label="2025-2026").first()
        for order, member in enumerate(TEAM_2025):
            photo = _copy("default", member["photo"], member["photo"])
            TeamMember.objects.create(
                season=season,
                order=order,
                name=member["name"],
                role_title=member["role_title"],
                email=member["email"],
                instagram_url=member["instagram_url"],
                linkedin_url=member["linkedin_url"],
                photo=photo,
            )

    if not TimelineEntry.objects.exists():
        for order, (date_label, title, body, image) in enumerate(TIMELINE):
            TimelineEntry.objects.create(
                order=order,
                date_label=date_label,
                title=title,
                body=body,
                image=_copy("default", image, image) if image else "",
            )

    if not Service.objects.exists():
        for order, (icon, title, body) in enumerate(SERVICES):
            Service.objects.create(order=order, icon=icon, title=title, body=body)

    for slug, title, body in PAGES:
        Page.objects.get_or_create(
            slug=slug,
            defaults={"title": title, "body": body.strip(), "show_in_footer": True},
        )

    if not FAQEntry.objects.exists():
        for order, (topic, question, answer) in enumerate(FAQ):
            FAQEntry.objects.create(order=order, topic=topic, question=question, answer=answer)


def backwards(apps, schema_editor):
    for model in ("TeamMember", "TimelineEntry", "Service", "FAQEntry", "Page"):
        apps.get_model("core", model).objects.all().delete()


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0001_initial"),
        ("memberships", "0002_seasons_and_legacy_memberships"),
    ]

    operations = [migrations.RunPython(forwards, backwards)]
