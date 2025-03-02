async function editOrderStatus(pk, value, callback = function(){}) {
    let action = "edit-order_status";
    let params = {
        token: api_token,
        action: action,
        pk: pk,
        value: value
    };
    
    let response = await sendApiRequest(params, "warehouse");
    
    if(response.status == "success") {
        callback(response);
    }
}

async function sendOrderStatusEmail(pk, callback = function(){}) {
    let action = "email-order_status";
    let message = document.querySelector("#custom_message");
    
    let params = {
        token: api_token,
        action: action,
        message: message.value,
        pk: pk,
    };
    
    let response = await sendApiRequest(params, "warehouse");
    
    if(response.status == "success") {
        callback(response);
    }
}

async function setItemAvailability(pk_order, pk_item, available, callback = function(){}) {
    let action = "set-itemAvailability";
    
    let params = {
        token: api_token,
        action: action,
        pk_order: pk_order,
        pk_item: pk_item,
        available: available
    };
    
    let response = await sendApiRequest(params, "warehouse");
    
    if(response.status == "success") {
        callback(response);
    }
}

async function writeNotes(pk_order, notes, callback = function(){}) {
    let action = "write-notes";
    
    let params = {
        token: api_token,
        action: action,
        pk_order: pk_order,
        notes: notes,
    };
    
    let response = await sendApiRequest(params, "warehouse");
    
    if(response.status == "success") {
        callback(response);
    }
}

function exportToPdf(order_pk) {
    var docDefinition = {
        info: {
            title: 'Contrat commande Magellans #' + order_pk,
            author: 'Magellans',
            subject: 'Contrat de commande',
            keywords: 'contrat, commande, Magellans'
        },
        content: []
    };

    let demandeur = $('#demandeur').text();
    let projet = $('#projet').text();
    let startDate = $('#startDate').text();
    let endDate = $('#endDate').text();
    let recuperation = $('#recuperation').text();
    let notes = $('#notes').val();

    // Ajouter un titre
    docDefinition.images = {logo: window.location.origin + "/static/img/logo_800x800.png"}
    docDefinition.content.push({ image: 'logo', width: 64, style: 'img'});
    docDefinition.content.push({ text: 'Récapitulatif commande Magellans #' + order_pk, style: 'header' });
    docDefinition.content.push({ text: 'Informations de la commande', style: 'subheader' });
    docDefinition.content.push({ text: "Demandeur : " + demandeur});
    docDefinition.content.push({ text: "Projet : " + projet});
    docDefinition.content.push({ text: 'Dates : ' + startDate + " à " + endDate});
    docDefinition.content.push({ text: "Récupération : " + recuperation});
    docDefinition.content.push({ text: 'Liste demandée', style: 'subheader' });
    
    // Récupérer les données du tableau
    var tableData = [['Dispo', 'Objet', '#']];
    
    $('#order-table tbody tr').each(function() {
        var rowData = [];
        $(this).find('td').each(function() {
            if($(this).children()[0]) {
                if($(this).children()[0].classList.contains('order-switch')) rowData.push($(this).children()[0].children[0].checked ? "Oui":"Non");
            }
            else {
                rowData.push($(this).text());
            }
        });
        tableData.push(rowData);
    });
    
    // Ajouter le tableau au document PDF
    docDefinition.content.push({
        table: {
            headerRows: 1,
            widths: [40, '*', 25],
            heights: 10,
            body: tableData
        }
    });

    docDefinition.content.push({ text: 'Notes supplémentaires', style: 'subheader' });
    docDefinition.content.push({ text: notes});

    
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
        }
    };
    
    // Personnaliser les cellules du tableau
    var body = docDefinition.content[8].table.body;
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
    my_pdf.getBlob((blob) => {
        const url = URL.createObjectURL(blob);
        const newTab = window.open(url, '_blank'); // Ouvre dans un nouvel onglet
    
        if (newTab) {
            setTimeout(() => URL.revokeObjectURL(url), 5000); // Nettoie après 5s
        } else {
            alert("Veuillez autoriser les pop-ups pour voir le PDF !");
        }
    });
    
    
}