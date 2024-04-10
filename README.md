# Magellans - le site internet
### Où suis-je ?
Ce répertoire contient les espaces de développement et de production du site [magellans.fr](https://magellans.fr).   
### Qui est Magellans ?
Magellans, c'est une association audiovisuelle composée de membres aux profils différents : des étudiants et des professionnels du secteur de l'audiovisuel, des comédiens… ou bien simplement des passionnés du cinéma et de l'audiovisuel !
Tous désireux d'apprendre de nouvelles choses, de rencontrer de nouvelles personnes… nous avons tous un but commun : réaliser sans cesse de nouveaux projets : des courts-métrages, des prestations tels que des captations d'évènements, des vidéos promotionnelles, des clips, et autres !
Ce qui fait notre force, c'est la diversité des profils de nos membres, leur volonté de se rapprocher au mieux d'un niveau professionnel et de relever constamment de nouveaux défis. Alors si l'aventure te tente, rejoins-nous !
## Contribuer
Ce fichier a pour but de vous expliquer comment installer localement ce projet afin que vous puissiez y contribuer.
### Dépendances & recommendations
Afin d'installer ce projet chez vous et de le faire fonctionner, vous aurez besoin d'installer [**Docker**](https://docs.docker.com/get-docker/) et son plugin [**Docker-compose**](https://docs.docker.com/compose/install/).

Nous vous conseillons fortement d'effectuer le développement sur une plateforme Unix (Ubuntu 23.10 ou Debian). 
Le projet utilise de nombreux langages de programmation différents, tels que : 
 - Python
 - JavaScript
 - HTML
 - CSS
 - Bash

Pour cette raison, nous vous conseillons d'utiliser l'IDE Visual Studio Code qui permet une grande flexibilité, nécessaire dans ce projet.
### Installation locale
Une fois toutes les dépendances installées, nous allons pouvoir installer et lancer le projet. 

Commencez par cloner ce répertoire, ou une fork que vous avez faite : 

    git clone git@github.com:Tonin386/magellans-site.git
Dans le nouveau dossier créé, vous devez créer deux fichiers supplémentaires :

 - /app/.env
 - mailserver.env
 
Voici le contenu initial du fichier `.env`,  qui doit se trouver dans le dossier `/app/` de votre projet. Vous pouvez le modifier pour satisfaire vos besoins :

    #Django configuration
    EMAIL_HOST='mail.server.com'
    EMAIL_PORT=587
    EMAIL_HOST_USER='admin@server.com'
    EMAIL_HOST_PASSWORD='123456789'
    EMAIL_RECEIVER='admin@server.com'
    
    DB_DJANGO_NAME='magellans-dj'
    DB_MAIL_NAME='magellans-mx'
    DB_USER='admin'
    DB_PASSWORD='123456789'
    DB_HOST='postgres-django'
    DB_PORT='5432'
    
    DEBUG='1' #Are you running the application in a dev or production environment?
    SECRET_KEY='your_secret_token'
    COMMAND='python manage.py runserver 0.0.0.0:8000' #in a dev environment
    #in a prod environment 'gunicorn magellans.asgi:application -b 0.0.0.0:8000 -w 4 -t 30 --reload -k uvicorn.workers.UvicornWorker -c gunicorn_config.py'
    
    NGINX_CONF_FILE='conf.d'  #conf_ssl.d #conf.d for dev, conf_ssl.d for prod
    STATICFILES_DIR='./app/assets/'
    
    #Email server configuration (not so usefull for dev environment)
    IMAP_HOST='ssl://mail.server.com'
    IMAP_PORT='993'
    SMTP_HOST='ssl://mail.server.com'
    SMTP_PORT='587'
    DNS_CHALLENGE_VALUE=''
    SSL_LETSENCRYPT='/etc/letsencrypt/'
    # SSL_CERTS_LIVE_DIR='/etc/letsencrypt/live/server.com' #only in production
Voici le contenu initial mais **facultatif** du fichier `mailserver.env` : [Lien vers Pastebin](https://pastebin.com/t2Tnwne9)
Tout a bien été configuré ! 

### Première exécution
La première fois que vous lancez le projet voici les commandes à exécuter **à la racine** du projet :

    ./run.sh db && ./run.sh in
Cette commande permet de créer les migrations initiales de la base de données, puis de vous placez dans la console du conteneur de Django où vous devrez créer un `superutilisateur` afin d'avoir accès à la plateforme d'administration.
Une fois dans cette console, exécutez la commande : 

    python manage.py createsuperuser
Et suivez les instructions qui s'affichent.
Ensuite, vous devrez modifier ce profil utilisateur pour lui attribuer le rôle de "Trésorier" sur le site. Il faut toujours au moins un trésorier sur le site. 
Retournez à la racine du projet. 

    ./run.sh python #placez vous dans la console python de Django
    from members.models import Member
    m = Member.objects.all()[0]
    m.role = 'T'
    m.save()
    exit()
    # exit
Voilà ! Le site devrait être fonctionnel. Vous pouvez y accéder à l'adresse `localhost` dans votre navigateur.
Happy coding!
