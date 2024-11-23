function addLocalExpense() {
    let name = document.querySelector("#expense_name").value.trim();
    let date = document.querySelector("#expense_date").value.trim();
    let amount = document.querySelector("#expense_amount").value.trim();
    let proof = document.querySelector("#expense_proof").files[0];
    let comm = document.querySelector("#expense_comm").value.trim();

    let formattedDate = Date.parse(date);

    const dateFormatter = new Intl.DateTimeFormat("fr-FR", {
        year: "numeric",
        month: "long",
        day: "numeric"
    });
    
    formattedDate = dateFormatter.format(formattedDate);
    
    if (name == "" || date == "" || amount == "") {
        
        createNotification(Math.floor(Math.random() * 1000000), "Champ manquant", "", "Veuillez compléter les champs requis avant d'ajouter la dépense.", 3)
        
        return; // Exit function if any required field is empty
    }
    
    // Creating card elements
    var card_container = document.createElement("div");
    card_container.classList.add("col-xl-3", "col-lg-4", "col-md-6", "my-1");
    
    let card = document.createElement("div");
    card.classList.add("card", "expenseCard");
    
    let cardHeader = document.createElement("div");
    cardHeader.classList.add("card-header", "bg-primary");
    
    let buttonDelete = document.createElement("button");
    buttonDelete.classList.add("btn", "btn-danger", "float-end");
    buttonDelete.type = "button";
    
    let trashIcon = document.createElement("i");
    trashIcon.classList.add("fa-solid", 'fa-trash');
    
    let cardBody = document.createElement("div");
    cardBody.classList.add("card-body");
    
    let cardTitle = document.createElement("h5");
    cardTitle.classList.add("float-start");
    cardTitle.textContent = name;
    
    let cardText = document.createElement("p");
    cardText.classList.add("card-text");
    cardText.innerHTML = "";
    
    if (proof) {
        cardText.innerHTML = `<strong>Justificatif : </strong>${proof['name']} <br>`;
    }


    cardText.innerHTML += `<strong>Date :</strong> ${formattedDate}<br><strong>Montant :</strong> ${amount}€<br> ${comm}`;
    
    buttonDelete.appendChild(trashIcon);
    
    // Appending elements to card body
    cardHeader.appendChild(cardTitle);
    cardHeader.appendChild(buttonDelete);
    cardBody.appendChild(cardText);
    
    // Appending card body to card
    card.appendChild(cardHeader);
    card.appendChild(cardBody);
    
    card_container.appendChild(card);
    
    // Appending card to the container
    document.getElementById("expenses").appendChild(card_container);
    
    var btnInvoice = $('#btnSubmitInvoice');
    btnInvoice.removeClass("disabled");
    
    function callback(response) {
        let id = response.id;
        var expensesInput = document.querySelector("#id_expenses_ids");
        expensesInput.value += id.toString() + ",";
        
        buttonDelete.onclick = function() {
            document.getElementById("expenses").removeChild(card_container);
            expensesInput.value = expensesInput.value.replace(',' + id.toString() + ',', ',');
        }
        
        document.querySelector("#expense_name").value = "";
        document.querySelector("#expense_date").value = "";
        document.querySelector("#expense_amount").value = "";
        document.querySelector("#expense_proof").value = "";
        document.querySelector("#expense_comm").value = "";
    }
    
    addExpense(name, date, amount, proof, comm, callback);
}

async function addExpense(name, date, amount, proof, comm, callback = function(){}) {
    let action = "add-expense";
    let params = {
        token: api_token,
        action: action,
        name: name,
        date: date,
        amount: amount,
        proof: proof,
        comm: comm,
    };
    
    if(params["proof"]) {
        const base64Image = await toBase64(params['proof']);
        params['proof'] = base64Image;
    }
    
    let response = await sendApiRequest(params, "bank");
    
    if(response.status == "success") {
        callback(response);
    }
}

