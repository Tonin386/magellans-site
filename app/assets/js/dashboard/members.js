async function addExtUser(callback = function(){}) {
    let action = "add-ext_user";
    let params = {
        token: api_token,
        action: action,
        first_name: document.querySelector("#ext-user_first_name").value,
        last_name: document.querySelector("#ext-user_last_name").value,
        email: document.querySelector("#ext-user_email").value,
        gender: document.querySelector("#ext-user_gender").value,
        phone: document.querySelector("#ext-user_phone").value,
        role: document.querySelector("#select_role").value
    };

    let response = await sendApiRequest(params, "members");

    if(response.status == "success") {
        callback(response);
    }
}

async function deleteExtUser(pk, callback = function(){}) {
    let action = "del-ext_user";
    let params = {
        token: api_token,
        action: action,
        pk: pk
    }

    let response = await sendApiRequest(params, "members");

    if(response.status == "success") {
        callback(response);
    }
}

async function editUserRole(pk, new_role, callback = function(){}) {
    let action = "edit-user_role";
    let params = {
        token: api_token,
        action: action,
        pk: pk,
        role: new_role
    }

    let response = await sendApiRequest(params, "members");

    if(response.status == "success") {
        callback(response);
    }
}

async function redirectExtPerson(pk_person, callback = function(){}) {
    let action = "redirect-ext_person";
    let params = {
        token: api_token,
        action: action,
        pk_person: pk_person,
        pk_member: document.querySelector("#select_redirect").value
    }

    let response = await sendApiRequest(params, "members");

    if(response.status == "success") {
        callback(response);
    }
}

async function resetMembers(callback = function(){}) {
    let action = "reset-members";

    let params = {
        token: api_token,
        action: action,
    }

    let response = await sendApiRequest(params, "members");

    if(response.status == "success") {
        callback(response);
    }
}