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
}

async function editItem(params) {
    params['action'] = "edit-item";
    params['token'] = api_token;

    let response = await sendApiRequest(params);
}

async function confirmDeleteItem(pk) {
    $('#confirmDeleteItemBtn').attr("value", pk);
    $('#confirmDeleteItemModal').modal('show');
}

async function deleteItem(pk) {
    let action = "del-item";
    let params = {
        token: api_token,
        action: action,
        pk: pk,
    }
    
    let response = await sendApiRequest(params);
    if(response.status == "success") {
        var itemList = document.querySelector("#item-list");
        let element = document.querySelector("#item" + pk.toString());
        itemList.removeChild(element);    
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
        let tagList = document.querySelector("#tag-list");
        
        let pk = response.created_pk;
        
        const div = document.createElement('div');
        div.classList.add('form-check', 'form-check-inline');
        div.id = `tag-group${pk}`;
        
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
}

async function confirmDeleteTags() {
    $('#confirmDeleteTagsModal').modal('show');
}

async function deleteTags() {
    let tagsBoxes = document.querySelectorAll("input.tag-checkbox");
    let selectedTags = [];
    
    tagsBoxes.forEach(tagBox => {
        if(tagBox.checked) {
            selectedTags.push(tagBox.value);
        }
    });
    
    let params = {
        token: api_token,
        action: "del-tag",
        pks: selectedTags
    }
    
    let response = await sendApiRequest(params);
    if(response.status == "success") {
        var tagList = document.querySelector("#tag-list");
        selectedTags.forEach(tag => {
            let element = document.querySelector("#tag-group" + tag.toString());
            tagList.removeChild(element);    
        });
    }
}

function colorAvailability(id = -1) {
    id = parseInt(id) || -1;
    var availabilitySelectors = document.querySelectorAll(".availability-selector");
    availabilitySelectors.forEach(selector => {

        let itemPk = selector.id.replace("stockSelectorItem", "");
        let value = selector.value;
        let max = selector.max;

        if(value >= max/2) {
            selector.parentElement.classList.remove("bg-warning");
            selector.parentElement.classList.remove("bg-danger");
            selector.parentElement.classList.add("bg-success");
        }
        else if(value < max/2 && value > 0) {
            selector.parentElement.classList.remove("bg-success");
            selector.parentElement.classList.remove("bg-danger");
            selector.parentElement.classList.add("bg-warning");
        }
        else if(value == 0) {
            selector.parentElement.classList.remove("bg-warning");
            selector.parentElement.classList.remove("bg-success");
            selector.parentElement.classList.add("bg-danger");
        }

        params = {
            now_available: value,
            pk: itemPk
        }

        if(id == itemPk) {
            editItem(params);
        }
    });
}

document.addEventListener('DOMContentLoaded', function() {
    
    var confirmDeleteItemBtn = $('#confirmDeleteItemBtn');
    $(confirmDeleteItemBtn).click(function (e) {
        deleteItem($(confirmDeleteItemBtn).attr("value"));
    });
    
    var availabilitySelectors = document.querySelectorAll(".availability-selector");
    availabilitySelectors.forEach(selector => {
        selector.addEventListener("input", function(event) {
            colorAvailability(selector.id.replace("stockSelectorItem", ""));
        });
    });

    colorAvailability();
});