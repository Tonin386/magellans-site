
function generateSignHash(projet, referent, date) {
    const data = projet + referent + date.toISOString();
    let hash = 0;
    for (let i = 0; i < data.length; i++) {
        const char = data.charCodeAt(i);
        hash = (hash << 5) - hash + char;
        hash |= 0; // Convert to 32bit integer
    }
    return Math.abs(hash).toString(16);
}

function generatePdfContract(order_pk, signed) {

    var docDefinition = {
        content: []
    };

    let demandeur = $('#demandeur').text();
    let projet = $('#projet').text();
    let startDate = $('#startDate').text();
    let endDate = $('#endDate').text();

    let real = $('#real-contrat').val();
    let telReal = $('#telReal-contrat').val();
    let emailReal = $('#emailReal-contrat').val();
    
    let prod = $('#prod-contrat').val();
    let adresse = $('#adresseProd-contrat').val();
    let telProd = $('#telProd-contrat').val();
    let emailProd = $('#emailProd-contrat').val();

    docDefinition.images = {
        logo: window.location.origin + "/static/img/logo_800x800.png",
        signAxelle: window.location.origin + "/static/img/signature-axelle.jpeg"
    };

    docDefinition.content.push({ image: 'logo', width: 64, style: 'img'});
    docDefinition.content.push({ text: 'Contrat commande Magellans #' + order_pk, style: 'header' });
    docDefinition.content.push({ text: 'Projet : ' + projet, style: 'header' });
    docDefinition.content.push({ text: 'Informations des différents tiers', style: 'subheader' });
    
    //infos réal
    docDefinition.content.push({ text: 'Réalisateur.ice : ' + real});
    docDefinition.content.push({ text: 'Téléphone du réalisateur.ice : ' + telReal});
    docDefinition.content.push({ text: 'Email du réalisateur.ice : ' + emailReal + '\n\n'});
    
    //info production
    docDefinition.content.push({ text: 'Production : ' + prod});
    if($('#telProd-contrat').val() != '') {
        docDefinition.content.push({ text: 'Adresse de la production : ' + adresse});
    }
    docDefinition.content.push({ text: 'Téléphone de la production : ' + telProd});
    docDefinition.content.push({ text: 'Email de la production : ' + emailProd + '\n\n'});
    
    //référent matériel
    docDefinition.content.push({ text: "Référent matériel : " + demandeur});
    
    //Informations de la location
    docDefinition.content.push({ text: 'Détails de la location/prêt', style: 'subheader' });
    
    docDefinition.content.push({ text: 'Dates de début et de fin de la location : \n\n'});
    docDefinition.content.push({ text: 'Du ' + startDate + " au " + endDate + '\n\n', style: 'boldCenter'});
    docDefinition.content.push({ text: 'Prise en charge sur site et retour du matériel sur le site.\n'});
    docDefinition.content.push({ text: 'Adresse du site : \n\n'});
    docDefinition.content.push({ text: '34 rue du Colonel Delorme, Montreuil\n\n', style: 'boldCenter'});
    
    docDefinition.content.push({text: "L’association MAGELLANS, siégée à Montreuil 93100 France, accorde, moyennant les contreparties visées ci-dessous, le prêt du matériel listé ci-dessous : \n\n"});
    
    // Récupérer les données du tableau
    var tableData = [['Objet', '#']];
        
    $('#order-table tbody tr').each(function() {
        var rowData = [];
        let objectOk = false;
        let countOk = false;
        $(this).find('td').each(function() {
            if($(this).children()[0]) {
                if($(this).children()[0].classList.contains('order-switch')) objectOk = $(this).children()[0].children[0].checked;
            }
            else {
                if(objectOk) {
                    rowData.push($(this).text());
                    objectOk = false;
                    countOk = true;
                }
                else if(countOk) {
                    rowData.push($(this).text());
                    objectOk = false;
                }
                else {
                    return;
                }
            }
        });

        if(rowData.length == 2) {
            tableData.push(rowData);
        }
    });

    // Ajouter le tableau au document PDF
    docDefinition.content.push({
        table: {
            headerRows: 1,
            widths: ['*', 25],
            heights: 10,
            body: tableData
        }
    });
    let table_index = docDefinition.content.length - 1;

    docDefinition.content.push({
        text: "\nÀ " + demandeur + " pour le projet " + projet + " réalisé par " + real + " et produit par " + prod + ".\n"
    });

    docDefinition.content.push({ text: '', pageBreak: 'after' });

    docDefinition.content.push({ text: 'Conditions générales du prêt', style: 'subheader' });
    docDefinition.content.push({
        text: "\nLe bénéficiaire s’engage à :",
    });

    const engagements = [
        "Utiliser le matériel référencé ci-dessus pour des tournages, sous son entière responsabilité, MAGELLANS ne pouvant être tenue pour responsable au titre du présent prêt pour quelque cause (défaillance, casse spontanée ou autre…) et conséquence que ce soit ;",
        "Tenir MAGELLANS au courant de tout dommage matériel (casse, bris…) qui pourrait affecter le matériel prêté pendant la durée du prêt ;",
        "Conserver le matériel sur le territoire (France) pendant toute la durée du prêt (sauf autorisation préalable écrite de MAGELLANS) ;",
        "En cas de perte ou de vol, utiliser la responsabilité civile et/ou l’assurance du référent de projet ou de la production ;",
        "Utiliser le matériel conformément à sa notice d’utilisation ;",
        "Sécuriser le matériel contre le vol ;",
        "Retourner le matériel à la date d’engagement précisée ci-dessous. A noter que le matériel demeure, pendant la durée du prêt, la propriété exclusive de MAGELLANS, et ne peut donc en aucun cas être cédé et/ou sous-loué à un tiers ;",
        "Informer sans délai MAGELLANS de tout problème qui pourrait affecter les matériels pendant la durée du prêt.",
    ];

    engagements.forEach((engagement) => {
        docDefinition.content.push({ text: '\n- ' + engagement, fontSize: 11 });
    });

    // Contreparties à fournir
    docDefinition.content.push({ text: 'Contreparties à fournir à MAGELLANS', style: 'subheader' });
    const contreparties = [
        "Fournir à MAGELLANS des photographies du tournage mettant en valeur la matériel prêté et son utilisation par les équipes du tournage, et autoriser MAGELLANS à utiliser ces images libres de tout droit en avance de phase par rapport à la sortie du film, étant entendu que ces images ne pourront pas dévoiler d’information quelconque sur l’intrigue du film, sauf accord préalable explicite de la production ;",
        "Autoriser MAGELLANS à utiliser ces images et témoignages libres de droits dans le cadre de sa communication vis-à-vis du grand public (sites internets, réseaux sociaux, newsletter…), de sa communication externe et interne, vis-à-vis de MAGELLANS ;",
        "Autoriser MAGELLANS à mettre en place des liens depuis ses sites internet et réseaux sociaux vers les sites internet sur lesquels le film ou des extraits de film ou de son making-of ou des interviews en relation avec le film et/ou le tournage et/ou sa promotion seront éventuellement déposés ;",
        "Élargir cette autorisation pour le(s) cas où le film serait nominé et/ou récompensé dans des festivals nationaux ou internationaux ;",
        "Citer le nom de MAGELLANS au générique de début et/ou fin du film, ainsi qu’à celui du making-of, parmis les autres partenaires du film ;",
        "Faire figurer le logo de MAGELLANS dans le générique de fin du film à côté des logos des autres partenaires et sponsors.",
    ];
    contreparties.forEach((contrepartie) => {
        docDefinition.content.push({ text: '\n- ' + contrepartie, fontSize: 11 });
    });

    if(signed) {
        // Signature
        docDefinition.content.push({ text: 'Signatures', style: 'subheader' });

        docDefinition.content.push({
            text: "\nDocument signé le : " + new Date().toLocaleDateString('fr-FR') + ",\n\n",
            style: "boldCenter"
        });

        docDefinition.content.push({
            columns: [
                { text: "par Axelle Servat, Magasinière Magellans", alignment: 'left' },
                { text:  "et", alignment: 'center' },
                { text:  demandeur, alignment: 'right' }
            ]
        });

        docDefinition.content.push({
            columns: [
                { image: 'signAxelle', width: 100, alignment: 'left' },
                { text: "Code de signature : " + generateSignHash(projet, demandeur, new Date()), alignment: 'right', color: 'blue' }
            ]
        });
    }

    // Styles personnalisés
    docDefinition.styles = {
        header: {
            fontSize: 18,
            bold: true,
            margin: [0, 10, 0, 10],
            color: 'black',
            alignment: "center"
        },
        subheader: {
            fontSize: 14,
            bold: true,
            margin: [0, 25, 0, 15],
            color: 'black',
            alignment: "left"
        },
        img: {
            alignment: "center"
        },
        boldCenter: {
            bold: true,
            alignment: 'center'
        },
    };
    
    // Personnaliser les cellules du tableau
    var body = docDefinition.content[table_index].table.body;
    for (var i = 1; i < body.length; i++) {
        for (var j = 0; j < body[i].length; j++) {
            if (i % 2 === 0) {
                body[i][j] = { text: body[i][j], fillColor: '#CCCCCC' };
            } else {
                body[i][j] = { text: body[i][j], fillColor: '#FFFFFF' };
            }
        }
    }
    
    // Générer le PDF
    const my_pdf = pdfMake.createPdf(docDefinition);
    const title = 'Contrat commande Magellans #' + order_pk + (signed ? ' signé':'') + '.pdf'
    my_pdf.download(title);

    if(signed) {
        my_pdf.getBuffer((buffer) => {
            sendContractByMail(order_pk, title, buffer);
        });
    }
}

async function sendContractByMail(pk_order, title, buffer, callback = function(){}) {
    let action = "email-sign_contract";

    let params = {
        token: api_token,
        action: action,
        pk_order: pk_order,
        title: title,
        pdfFileBase64: buffer.toString('base64'),
    };
    
    let response = await sendApiRequest(params, "warehouse");
    
    if(response.status == "success") {
        callback(response);

        setTimeout(() => { location.reload() }, 2000);
    }
}