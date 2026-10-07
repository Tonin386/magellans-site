"""Contenus et paramètres du site, éditables par le CA depuis l'espace CA."""

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.cache import cache
from django.db import models
from django.urls import reverse
from django.utils import timezone

from .storage import private_storage

SITE_SETTINGS_CACHE_KEY = "core:site-settings:v1"


def lines(text):
    """Découpe un champ texte « une valeur par ligne » en liste propre."""
    return [line.strip() for line in (text or "").splitlines() if line.strip()]


class SiteSettings(models.Model):
    """Paramètres généraux du site (une seule ligne, pk=1)."""

    TONE_CHOICES = [
        ("brand", "Magellans (ambre)"),
        ("info", "Information (bleu)"),
        ("success", "Bonne nouvelle (vert)"),
        ("warning", "Attention (orange)"),
    ]
    THEME_CHOICES = [
        ("none", "Aucun"),
        ("winter", "Hiver (flocons de neige)"),
        ("halloween", "Halloween"),
    ]

    # --- Identité ----------------------------------------------------------
    site_name = models.CharField("Nom de l'association", max_length=80, default="Magellans")
    tagline = models.CharField(
        "Accroche courte", max_length=200, default="Association audiovisuelle en région parisienne"
    )
    meta_description = models.TextField(
        "Description pour les moteurs de recherche",
        default=(
            "Magellans est une association d'audiovisuel basée à Montreuil. En adhérant, tu accèdes à "
            "son magasin de matériel, tu participes à des tournages et tu rencontres d'autres passionné·es."
        ),
    )
    founded_year = models.PositiveSmallIntegerField("Année de création", default=2020)
    rna_number = models.CharField("Numéro RNA", max_length=20, blank=True, default="W931023484")
    address = models.CharField("Adresse", max_length=200, blank=True, default="34 rue du Colonel Delorme")
    postal_code = models.CharField("Code postal", max_length=10, blank=True, default="93100")
    city = models.CharField("Ville", max_length=80, blank=True, default="Montreuil")

    # --- Page d'accueil ----------------------------------------------------
    hero_kicker = models.CharField("Surtitre", max_length=120, default="Bienvenue dans Magellans !")
    hero_title = models.CharField("Titre principal", max_length=120, default="Rejoins notre aventure")
    hero_text = models.TextField(
        "Texte d'introduction",
        default=(
            "Courts-métrages, clips, captations, documentaires… Magellans réunit étudiant·es, "
            "professionnel·les et passionné·es pour faire des films ensemble."
        ),
    )
    hero_video = models.FileField(
        "Vidéo d'arrière-plan",
        upload_to="site/",
        blank=True,
        help_text="MP4 léger (moins de 10 Mo). Laisser vide pour la vidéo par défaut.",
    )
    hero_image = models.ImageField(
        "Image d'arrière-plan / affiche de la vidéo", upload_to="site/", blank=True
    )
    about_title = models.CharField("Titre « À propos »", max_length=120, default="Magellans, c'est quoi ?")
    about_text = models.TextField(
        "Texte « À propos » (Markdown)",
        default=(
            "Magellans, c'est une association audiovisuelle basée en région parisienne composée de membres "
            "aux profils différents : des étudiant·es et des professionnel·les du secteur de l'audiovisuel, "
            "des comédien·nes… ou bien simplement des passionné·es du cinéma et de l'audiovisuel.\n\n"
            "Tous désireux d'apprendre de nouvelles choses, de rencontrer de nouvelles personnes… Nous avons "
            "tous un but commun : réaliser sans cesse de nouveaux projets. Des courts-métrages, des "
            "prestations telles que des captations d'évènements, des vidéos promotionnelles, des clips, et "
            "bien d'autres.\n\n"
            "Ce qui fait notre force, c'est la diversité des profils de nos membres, leur volonté de se "
            "rapprocher au mieux d'un niveau professionnel et de relever constamment de nouveaux défis. "
            "Alors si l'aventure te tente, rejoins-nous !"
        ),
    )
    photo_credits = models.TextField(
        "Crédits photos",
        blank=True,
        default=(
            "Axelle Servat | https://www.instagram.com/axelleservat/\n"
            "Héloïse Abbosh | https://www.instagram.com/heloise.ah/"
        ),
        help_text="Une personne par ligne, au format « Nom | lien (facultatif) ».",
    )

    # --- Contact & réseaux -------------------------------------------------
    contact_email = models.EmailField("E-mail de contact public", default="contact@magellans.fr")
    contact_phone = models.CharField("Téléphone de contact public", max_length=30, blank=True)
    instagram_url = models.URLField("Instagram", blank=True, default="https://www.instagram.com/magellansproject/")
    tiktok_url = models.URLField("TikTok", blank=True, default="https://www.tiktok.com/@magellansproject")
    youtube_url = models.URLField(
        "YouTube", blank=True, default="https://www.youtube.com/channel/UCLU4qQfiuMThtss8TKoZx5Q"
    )
    twitch_url = models.URLField("Twitch", blank=True, default="https://www.twitch.tv/magellans_project")
    discord_url = models.URLField("Discord", blank=True, default="https://discord.gg/Fdqr8mhxEE")
    linkedin_url = models.URLField("LinkedIn", blank=True)
    donation_url = models.URLField(
        "Lien « Faire un don » (HelloAsso)",
        blank=True,
        default="https://www.helloasso.com/associations/magellans/formulaires/1",
    )

    # --- Destinataires des notifications ------------------------------------
    notify_contact = models.TextField(
        "Formulaire de contact",
        default="contact@magellans.fr",
        help_text="Une adresse par ligne.",
    )
    notify_orders = models.TextField(
        "Nouvelles réservations du magasin",
        blank=True,
        default="contact@magellans.fr",
        help_text="Une adresse par ligne. Les gestionnaires du magasin sont toujours prévenus.",
    )
    notify_memberships = models.TextField(
        "Nouvelles adhésions", blank=True, default="contact@magellans.fr", help_text="Une adresse par ligne."
    )
    notify_finance = models.TextField(
        "Notes de frais",
        blank=True,
        help_text="Une adresse par ligne. Les trésorier·ères sont toujours prévenu·es.",
    )
    notify_funding = models.TextField(
        "Demandes d'aide à projet", blank=True, default="contact@magellans.fr", help_text="Une adresse par ligne."
    )

    # --- Annonce & mise en avant -------------------------------------------
    announcement_enabled = models.BooleanField("Afficher le bandeau d'annonce", default=False)
    announcement_text = models.CharField("Texte du bandeau", max_length=240, blank=True)
    announcement_link_label = models.CharField("Texte du lien", max_length=60, blank=True)
    announcement_link_url = models.CharField("Adresse du lien", max_length=300, blank=True)
    announcement_tone = models.CharField("Couleur", max_length=10, choices=TONE_CHOICES, default="brand")
    spotlight_enabled = models.BooleanField("Afficher la mise en avant sur l'accueil", default=False)
    spotlight_title = models.CharField("Titre de la mise en avant", max_length=120, blank=True)
    spotlight_text = models.TextField("Texte de la mise en avant", blank=True)
    spotlight_video_url = models.URLField(
        "Vidéo (YouTube ou Vimeo)", blank=True, help_text="Ex. le dernier film sorti."
    )
    seasonal_theme = models.CharField("Thème saisonnier", max_length=12, choices=THEME_CHOICES, default="none")

    # --- Magasin -------------------------------------------------------------
    warehouse_enabled = models.BooleanField("Réservations ouvertes", default=True)
    warehouse_members_only = models.BooleanField(
        "Réservations réservées aux adhérent·es à jour",
        default=False,
        help_text="Si coché, seules les personnes ayant adhéré pour la saison en cours peuvent réserver.",
    )
    warehouse_notice = models.TextField(
        "Message affiché sur le catalogue",
        blank=True,
        default=(
            "Le matériel est prêté gratuitement aux membres. Choisis tes dates, ajoute le matériel "
            "à ta demande puis envoie-la : l'équipe du magasin te répond rapidement."
        ),
    )
    order_cooldown_minutes = models.PositiveIntegerField(
        "Délai minimum entre deux demandes (minutes)", default=60
    )
    order_min_notice_hours = models.PositiveIntegerField(
        "Délai de prévenance minimum (heures)",
        default=24,
        help_text="Une demande doit commencer au moins ce nombre d'heures après son envoi.",
    )
    order_max_days = models.PositiveIntegerField(
        "Durée maximale d'un prêt (jours)", default=21, help_text="0 = pas de limite."
    )
    pickup_address = models.CharField(
        "Adresse de retrait du matériel", max_length=200, default="34 rue du Colonel Delorme, 93100 Montreuil"
    )
    pickup_instructions = models.TextField("Instructions de retrait", blank=True)

    # --- Contrat de prêt ----------------------------------------------------
    contract_signatory_name = models.CharField(
        "Signataire pour Magellans", max_length=120, default="Axelle Servat"
    )
    contract_signatory_title = models.CharField(
        "Fonction du signataire", max_length=120, default="Magasinière Magellans"
    )
    contract_signature = models.ImageField(
        "Signature (image)",
        upload_to="site/signature/",
        storage=private_storage,
        blank=True,
        help_text="Image privée, uniquement intégrée aux contrats générés.",
    )
    contract_intro = models.TextField(
        "Préambule du contrat",
        default=(
            "L'association MAGELLANS, dont le siège est à Montreuil (93100, France), accorde, moyennant les "
            "contreparties visées ci-dessous, le prêt du matériel listé ci-dessous."
        ),
    )
    contract_commitments = models.TextField(
        "Engagements du bénéficiaire (un par ligne)",
        default="\n".join(
            [
                "Utiliser le matériel référencé ci-dessus pour des tournages, sous son entière responsabilité, MAGELLANS ne pouvant être tenue pour responsable au titre du présent prêt pour quelque cause (défaillance, casse spontanée ou autre…) et conséquence que ce soit ;",
                "Tenir MAGELLANS au courant de tout dommage matériel (casse, bris…) qui pourrait affecter le matériel prêté pendant la durée du prêt ;",
                "Conserver le matériel sur le territoire (France) pendant toute la durée du prêt (sauf autorisation préalable écrite de MAGELLANS) ;",
                "En cas de perte ou de vol, utiliser la responsabilité civile et/ou l'assurance du référent de projet ou de la production ;",
                "Utiliser le matériel conformément à sa notice d'utilisation ;",
                "Sécuriser le matériel contre le vol ;",
                "Retourner le matériel à la date d'engagement précisée ci-dessus. Le matériel demeure, pendant la durée du prêt, la propriété exclusive de MAGELLANS, et ne peut donc en aucun cas être cédé et/ou sous-loué à un tiers ;",
                "Informer sans délai MAGELLANS de tout problème qui pourrait affecter les matériels pendant la durée du prêt.",
            ]
        ),
    )
    contract_counterparts = models.TextField(
        "Contreparties pour Magellans (une par ligne)",
        default="\n".join(
            [
                "Fournir à MAGELLANS des photographies du tournage mettant en valeur le matériel prêté et son utilisation par les équipes du tournage, et autoriser MAGELLANS à utiliser ces images libres de tout droit en avance de phase par rapport à la sortie du film, étant entendu que ces images ne pourront pas dévoiler d'information quelconque sur l'intrigue du film, sauf accord préalable explicite de la production ;",
                "Autoriser MAGELLANS à utiliser ces images et témoignages libres de droits dans le cadre de sa communication vis-à-vis du grand public (sites internet, réseaux sociaux, newsletter…), de sa communication externe et interne ;",
                "Autoriser MAGELLANS à mettre en place des liens depuis ses sites internet et réseaux sociaux vers les sites internet sur lesquels le film ou des extraits du film ou de son making-of ou des interviews en relation avec le film et/ou le tournage et/ou sa promotion seront éventuellement déposés ;",
                "Élargir cette autorisation pour le(s) cas où le film serait nominé et/ou récompensé dans des festivals nationaux ou internationaux ;",
                "Citer le nom de MAGELLANS au générique de début et/ou de fin du film, ainsi qu'à celui du making-of, parmi les autres partenaires du film ;",
                "Faire figurer le logo de MAGELLANS dans le générique de fin du film à côté des logos des autres partenaires et sponsors.",
            ]
        ),
    )

    # --- Aides & notes de frais --------------------------------------------
    funding_max_amount = models.PositiveIntegerField("Montant maximum d'une aide à projet (€)", default=500)
    funding_intro = models.TextField(
        "Explications – demande d'aide (Markdown)",
        default=(
            "Cette page te permet de présenter ton projet et de demander une aide financière à Magellans. "
            "Ta demande sera examinée lors d'une prochaine réunion du conseil d'administration. "
            "Merci de transmettre tous les documents au format PDF."
        ),
    )
    expense_intro = models.TextField(
        "Explications – notes de frais (Markdown)",
        default=(
            "Tu as avancé des frais sur un projet en partenariat avec Magellans ? Déclare-les ici, avec "
            "un justificatif pour chaque dépense, et la trésorerie te recontactera pour le remboursement.\n\n"
            "- Fais une seule note de frais par projet.\n"
            "- Sans justificatif, le remboursement ne pourra pas être effectué.\n"
            "- **Attention :** un ticket de carte bancaire n'est **pas** un justificatif."
        ),
    )

    # --- Adhésions -----------------------------------------------------------
    membership_auto_accounts = models.BooleanField(
        "Créer automatiquement un compte pour chaque nouvel·le adhérent·e",
        default=True,
        help_text="Un e-mail d'invitation permet ensuite de choisir son mot de passe.",
    )

    # --- Avancé --------------------------------------------------------------
    ga_measurement_id = models.CharField(
        "Identifiant Google Analytics",
        max_length=30,
        blank=True,
        default="G-BDZJKQJ88M",
        help_text="Chargé uniquement après accord des visiteurs (bandeau de consentement). Laisser vide pour désactiver.",
    )
    maintenance_mode = models.BooleanField(
        "Mode maintenance",
        default=False,
        help_text="Le site public affiche une page de maintenance. Les membres du CA gardent l'accès.",
    )
    maintenance_message = models.TextField(
        "Message de maintenance",
        blank=True,
        default="Nous revenons très vite ! En attendant, retrouve-nous sur Instagram.",
    )

    updated_at = models.DateTimeField("Dernière modification", auto_now=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="Modifié par",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )

    class Meta:
        verbose_name = "Paramètres du site"
        verbose_name_plural = "Paramètres du site"

    def __str__(self):
        return "Paramètres du site"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)
        cache.delete(SITE_SETTINGS_CACHE_KEY)

    def delete(self, *args, **kwargs):  # pragma: no cover - garde-fou
        raise RuntimeError("Les paramètres du site ne peuvent pas être supprimés.")

    @classmethod
    def load(cls):
        obj = cache.get(SITE_SETTINGS_CACHE_KEY)
        if obj is None:
            obj, _ = cls.objects.get_or_create(pk=1)
            cache.set(SITE_SETTINGS_CACHE_KEY, obj, 300)
        return obj

    # Aides pour les gabarits ------------------------------------------------
    @property
    def full_address(self):
        return ", ".join(part for part in [self.address, f"{self.postal_code} {self.city}".strip()] if part)

    @property
    def social_links(self):
        candidates = [
            ("instagram", "Instagram", self.instagram_url),
            ("tiktok", "TikTok", self.tiktok_url),
            ("youtube", "YouTube", self.youtube_url),
            ("twitch", "Twitch", self.twitch_url),
            ("discord", "Discord", self.discord_url),
            ("linkedin", "LinkedIn", self.linkedin_url),
        ]
        return [{"key": key, "label": label, "url": url} for key, label, url in candidates if url]

    @property
    def photo_credit_list(self):
        credits = []
        for line in lines(self.photo_credits):
            name, _, url = line.partition("|")
            credits.append({"name": name.strip(), "url": url.strip()})
        return credits

    @property
    def contract_commitment_list(self):
        return lines(self.contract_commitments)

    @property
    def contract_counterpart_list(self):
        return lines(self.contract_counterparts)

    def recipients(self, field):
        return lines(getattr(self, f"notify_{field}"))


class OrderedModel(models.Model):
    order = models.PositiveSmallIntegerField("Ordre d'affichage", default=0)
    is_visible = models.BooleanField("Visible sur le site", default=True)

    class Meta:
        abstract = True
        ordering = ["order", "pk"]


class TeamMember(OrderedModel):
    """Membre de l'équipe (CA) présenté sur la page d'accueil."""

    season = models.ForeignKey(
        "memberships.Season",
        verbose_name="Saison",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="team_members",
        help_text="L'accueil affiche l'équipe de la saison en cours (ou, à défaut, la plus récente).",
    )
    person = models.ForeignKey(
        "members.Person",
        verbose_name="Fiche personne liée",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="team_entries",
    )
    name = models.CharField("Nom affiché", max_length=120)
    role_title = models.CharField("Fonction affichée", max_length=120)
    photo = models.ImageField("Photo", upload_to="team/", blank=True)
    email = models.EmailField("E-mail public", blank=True)
    bio = models.CharField("Courte présentation", max_length=280, blank=True)
    instagram_url = models.URLField("Instagram", blank=True)
    linkedin_url = models.URLField("LinkedIn", blank=True)

    class Meta(OrderedModel.Meta):
        verbose_name = "Membre de l'équipe"
        verbose_name_plural = "Équipe"

    def __str__(self):
        return f"{self.name} — {self.role_title}"

    @property
    def initials(self):
        return "".join(part[0] for part in self.name.split()[:2]).upper()


class TimelineEntry(OrderedModel):
    date_label = models.CharField("Date", max_length=60, help_text="Ex. « Septembre 2020 »")
    title = models.CharField("Titre", max_length=120)
    body = models.TextField("Texte")
    image = models.ImageField("Illustration", upload_to="timeline/", blank=True)

    class Meta(OrderedModel.Meta):
        verbose_name = "Étape de l'historique"
        verbose_name_plural = "Historique"

    def __str__(self):
        return f"{self.date_label} — {self.title}"


class Service(OrderedModel):
    ICON_CHOICES = [
        ("users", "Réseau / personnes"),
        ("send", "Projet / envoi"),
        ("package", "Matériel"),
        ("clapperboard", "Clap de cinéma"),
        ("camera", "Caméra"),
        ("video", "Vidéo"),
        ("mic", "Micro"),
        ("graduation-cap", "Formation"),
        ("sparkles", "Étincelles"),
        ("heart-handshake", "Entraide"),
        ("calendar", "Évènement"),
        ("trophy", "Festival / prix"),
    ]
    icon = models.CharField("Icône", max_length=40, choices=ICON_CHOICES, default="sparkles")
    title = models.CharField("Titre", max_length=80)
    body = models.TextField("Texte")

    class Meta(OrderedModel.Meta):
        verbose_name = "Service"
        verbose_name_plural = "Services"

    def __str__(self):
        return self.title


class Page(models.Model):
    """Page de contenu libre (mentions légales, confidentialité, CGU…)."""

    slug = models.SlugField("Adresse", max_length=80, unique=True)
    title = models.CharField("Titre", max_length=120)
    body = models.TextField("Contenu (Markdown)")
    show_in_footer = models.BooleanField("Lien dans le pied de page", default=True)
    is_published = models.BooleanField("Publiée", default=True)
    needs_review = models.BooleanField(
        "À relire par le CA",
        default=False,
        help_text="Indique un texte proposé par défaut qui doit être validé par le CA.",
    )
    updated_at = models.DateTimeField("Dernière modification", auto_now=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )

    class Meta:
        verbose_name = "Page"
        ordering = ["title"]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("page", kwargs={"slug": self.slug})


class FAQEntry(OrderedModel):
    TOPIC_CHOICES = [
        ("membership", "Adhésion"),
        ("warehouse", "Magasin"),
        ("projects", "Projets & aides"),
        ("general", "Général"),
    ]
    topic = models.CharField("Thème", max_length=20, choices=TOPIC_CHOICES, default="membership")
    question = models.CharField("Question", max_length=200)
    answer = models.TextField("Réponse (Markdown)")

    class Meta(OrderedModel.Meta):
        verbose_name = "Question fréquente"
        verbose_name_plural = "Questions fréquentes"

    def __str__(self):
        return self.question


class ActivityLog(models.Model):
    """Journal des actions effectuées sur le site (qui a fait quoi, quand)."""

    CATEGORY_CHOICES = [
        ("memberships", "Adhésions"),
        ("people", "Personnes"),
        ("warehouse", "Magasin"),
        ("finance", "Trésorerie"),
        ("projects", "Projets"),
        ("funding", "Aides à projet"),
        ("resources", "Ressources"),
        ("content", "Contenus du site"),
        ("account", "Comptes"),
        ("system", "Système"),
    ]

    created_at = models.DateTimeField("Date", default=timezone.now, db_index=True)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="Auteur",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="activity",
    )
    category = models.CharField("Domaine", max_length=20, choices=CATEGORY_CHOICES, default="system")
    verb = models.CharField("Action", max_length=40)
    message = models.TextField("Description")
    target_type = models.ForeignKey(ContentType, null=True, blank=True, on_delete=models.SET_NULL)
    target_id = models.CharField(max_length=64, blank=True)
    target_repr = models.CharField("Objet", max_length=255, blank=True)
    data = models.JSONField("Détails", default=dict, blank=True)
    ip_address = models.GenericIPAddressField("Adresse IP", null=True, blank=True)

    class Meta:
        verbose_name = "Entrée du journal"
        verbose_name_plural = "Journal d'activité"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.created_at:%d/%m/%Y %H:%M} — {self.message}"


class Message(models.Model):
    """Message d'un fil de discussion attaché à un objet (réservation, note de frais…)."""

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.CharField(max_length=64)
    target = GenericForeignKey("content_type", "object_id")
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="Auteur",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="thread_messages",
    )
    body = models.TextField("Message")
    is_internal = models.BooleanField(
        "Note interne au CA", default=False, help_text="Invisible pour la personne concernée."
    )
    is_from_board = models.BooleanField("Envoyé par le CA", default=False)
    created_at = models.DateTimeField("Date", default=timezone.now)

    class Meta:
        verbose_name = "Message"
        ordering = ["created_at", "pk"]
        indexes = [models.Index(fields=["content_type", "object_id"])]

    def __str__(self):
        return f"Message de {self.author} ({self.created_at:%d/%m/%Y})"
