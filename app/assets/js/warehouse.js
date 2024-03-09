const toBase64 = file => new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.readAsDataURL(file);
    reader.onload = () => resolve(reader.result);
    reader.onerror = reject;
});

function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = jQuery.trim(cookies[i]);
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function printApiToken() {
    console.log(api_token);
}

async function sendApiRequest(params) {
    const url = window.location.origin + "/api/warehouse";
    let request = {
        method: "POST",
        body: JSON.stringify(params),
        headers: {
            "X-CSRFToken": getCookie("csrftoken"),
            "Accept": "application/json",
            "Content-type": "application/json; charset=UTF-8",
            'X-Requested-With': 'XMLHttpRequest',
        }
    }
    
    try {
        let response = await fetch(url, request);
        if(!response.ok) {
            throw new Error('Failed to fetch api response');
        }
        
        const data = await response.json();
        return data;
    }
    catch (error){
        console.log(error);
    }
} 

async function addItem() {
    let action = "add-item";
    let params = {
        token: api_token,
        action: action,
        name: document.querySelector("#item_name").value,
        tags: [],
        image: document.querySelector("#image").files[0],
        max_stock: document.querySelector("#max_stock").value,
        state: document.querySelector('#state').value,
        availability: document.querySelector("#availability").value
    };
    
    if(params["image"]) {
        const base64Image = await toBase64(params['image']);
        params['image'] = base64Image;
    }
    
    let tagsCheckboxes = document.querySelectorAll(".tag-checkbox");
    tagsCheckboxes.forEach(tag => {
        if(tag.checked) {
            params.tags.push(tag.value);
        }
    });
    
    let response = await sendApiRequest(params);
    
    if(response.status == "success") {
        const toastItemSuccess = document.querySelector("#addItemSuccess");
        const toastBootstrap = bootstrap.Toast.getOrCreateInstance(toastItemSuccess);
        toastBootstrap.show();
    }
    else if(response.status == "error") {
        const toastItemError = document.querySelector("#addItemError");
        const toastBootstrap = bootstrap.Toast.getOrCreateInstance(toastItemSuccess);
        toastBootstrap.show();
    }
}

async function addTag() {
    let action = "add-tag";
    let params = {
        token: api_token,
        action: action,
        name: document.querySelector("#tag_name").value,
        color: document.querySelector("#tag_color").value
    };
    
    let response = await sendApiRequest(params);
    
    if(response.status == "success") {
        const toastTagSuccess = document.querySelector("#addTagSuccess");
        const toastBootstrap = bootstrap.Toast.getOrCreateInstance(toastTagSuccess);
        toastBootstrap.show();
        
        let tagList = document.querySelector("#tag_list");

        let pk = response.created_pk;

        const div = document.createElement('div');
        div.classList.add('form-check', 'form-check-inline');
        
        const input = document.createElement('input');
        input.type = 'checkbox';
        input.value = pk;
        input.classList.add('tag-checkbox', 'form-check-input');
        input.id = `tag${pk}`;
        
        const label = document.createElement('label');
        label.classList.add('btn', 'form-check-label');
        label.setAttribute('for', `tag${pk}`);
        label.style.backgroundColor = params.color;
        label.style.color = 'white';
        label.textContent = params.name;
        
        // Append the elements to the div
        div.appendChild(input);
        div.appendChild(label);
        
        // Append the div to the tagList
        tagList.appendChild(div);
    }
    else if(response.status == "error") {
        const toastTagError = document.querySelector("#addTagError");
        const toastBootstrap = bootstrap.Toast.getOrCreateInstance(toastTagSuccess);
        toastBootstrap.show();
    }
}