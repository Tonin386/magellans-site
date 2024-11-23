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
    
    let response = await sendApiRequest(params, "warehouse");
}

async function editItem(params) {
    params['action'] = "edit-item";
    params['token'] = api_token;
    
    let response = await sendApiRequest(params, "warehouse");
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
    
    let response = await sendApiRequest(params, "warehouse");
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
    
    let response = await sendApiRequest(params, "warehouse");
    
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
    
    let response = await sendApiRequest(params, "warehouse");
    if(response.status == "success") {
        var tagList = document.querySelector("#tag-list");
        selectedTags.forEach(tag => {
            let element = document.querySelector("#tag-group" + tag.toString());
            tagList.removeChild(element);    
        });
    }
}

async function addItemToTempOrder(pk_order, pk_item) {
    let action = "add-item-tempOrder";
    let params = {
        token: api_token,
        action: action,
        pk_order: pk_order,
        pk_item: pk_item,
    }

    let response = await sendApiRequest(params, "warehouse");

    if(response.status == "success") {
        let button = document.querySelector("#addItemOrderBtn" + pk_item);

        let totalItems = response.total_items;
        document.querySelector("#nbOrderedItems").innerText = totalItems;

        let newCount = response.new_count;

        if($(button).attr('max') <= newCount) {
            button.disabled = true;
        }

        let orderCount = document.querySelector("#itemOrderCount" + pk_item);
        orderCount.innerText = newCount;

        let friendButton = document.querySelector("#removeItemOrderBtn" + pk_item);
        if(friendButton.disabled) {
            $(friendButton).removeAttr("disabled");
        }
    }
}

async function removeItemFromTempOrder(pk_order, pk_item) {
    let action = "remove-item-tempOrder";
    let params = {
        token: api_token,
        action: action,
        pk_order: pk_order,
        pk_item: pk_item,
    }

    let response = await sendApiRequest(params, "warehouse");

    if(response.status == "success") {
        let button = document.querySelector("#removeItemOrderBtn" + pk_item);

        let totalItems = response.total_items;
        document.querySelector("#nbOrderedItems").innerText = totalItems;

        let newCount = response.new_count;
        if(newCount <= 0) {
            button.disabled = true;
        }

        let orderCount = document.querySelector("#itemOrderCount" + pk_item);
        orderCount.innerText = newCount;

        let friendButton = document.querySelector("#addItemOrderBtn" + pk_item);
        if(friendButton.disabled) {
            $(friendButton).removeAttr("disabled");
        }
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

function filterSearchItems(text) {
    itemsMatchingSearch = [];
    text = text.toLowerCase();
    itemDatabase.forEach(item => {
        if(text == "") {
            itemsMatchingSearch.push(item.id);
        }
        else if(item.completeText.includes(text)) {
            itemsMatchingSearch.push(item.id);
        }
    });
    
    displayItems();
}

function filterTagItems() {
    var selectedTags = [];
    itemsMatchingTags = [];
    tagSelectButtons.forEach(tagSelectButton => {
        if(tagSelectButton.checked) {
            selectedTags.push($(tagSelectButton).attr('value'));
        }
    });

    itemDatabase.forEach(item => {
        if(selectedTags.length == 0 || selectedTags.length == tagSelectButtons.length) {
            itemsMatchingTags.push(item.id);
            return;
        }

        var showItem = false;

        selectedTags.forEach(selectedTag => {
            if(item.tagNames.includes(selectedTag)) {
                showItem = true;
                return;
            }
        });

        if(showItem && item.tagNames.length > 0) {
            itemsMatchingTags.push(item.id);
        }
    });
    
    displayItems();
}

function displayItems() {
    itemDatabase.forEach(item => {
        if(itemsMatchingSearch.includes(item.id) && itemsMatchingTags.includes(item.id)) {
            item.parentElement.classList.remove("d-none");
        }
        else {
            if(!item.parentElement.classList.contains("d-none")) {
                item.parentElement.classList.add("d-none");
            }
        }
    });
}

var tagSelectButtons = [];
var itemsCards = [];
var itemDatabase = [];
var itemsMatchingSearch = [];
var itemsMatchingTags = [];

document.addEventListener('DOMContentLoaded', function() {
    
    tagSelectButtons = document.querySelectorAll(".selectedTag-checkbox");
    itemsCards = document.querySelectorAll(".tag-card");
    
    itemsCards.forEach(itemCard => {
        let parentElement = itemCard.parentElement;
        let title = itemCard.querySelector(".card-title").innerText;
        let tagNames = [];
        let completeText = title;
        itemCard.querySelectorAll(".badge-tag").forEach(btn => {
            tagNames.push(btn.innerText);
            completeText += " " + btn.innerText;
        });
        
        itemDatabase.push({
            id:  parentElement.id,
            parentElement: parentElement,
            title: title,
            tagNames: tagNames,
            completeText: completeText.toLowerCase()
        });
        
        itemsMatchingSearch.push(parentElement.id);
        itemsMatchingTags.push(parentElement.id);
    });
    
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
    
    tagSelectButtons.forEach(button => {
        button.addEventListener("change", function(event) {
            filterTagItems();
        })
    });
    
    var searchBar = document.querySelector("#searchBar");
    searchBar.addEventListener("input", function(event) {
        filterSearchItems(event.target.value);
    });

    colorAvailability();
});