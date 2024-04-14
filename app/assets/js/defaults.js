var monthFrNames = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre", "décembre"];
function convertFrDate(str_date) {

    let parts = str_date.split(' ');
    let day = parseInt(parts[0], 10);
    let month = monthFrNames.indexOf(parts[1]);
    let year = parseInt(parts[2], 10);

    let date = new Date(year, month, day);

    return date;
}

function convertFrDatetime(str_datetime) {
    let parts = str_datetime.split(' ');
    let day = parseInt(parts[0], 10);
    let month = monthFrNames.indexOf(parts[1]);
    let year = parseInt(parts[2], 10);
    let time = parts[3].split(':');
    let hour = parseInt(time[0], 10);
    let minute = parseInt(time[1], 10);

    let date = new Date(year, month, day, hour, minute);

    return date;
}

$.extend($.fn.dataTable.defaults, {
    paging: true,
    searching: true,
    ordering: true,
    lengthMenu: [ [10,25,50,-1], [10,25,50,"All"] ],
    stateSave: true,
    language: {
        url: "https://cdn.datatables.net/plug-ins/1.10.24/i18n/French.json"
    },
    responsive: true,
    initComplete: function(settings, json) {
        this.responsive.recalc();
    },
    pagingType: "numbers"
})

$.extend($.fn.dataTableExt.oSort, {
    "ope-desc": function (a, b) {
        var numA = parseInt(a.replace('OPE-', ''), 10);
        var numB = parseInt(b.replace('OPE-', ''), 10);
        
        return numB - numA;
    },
    
    "ope-asc": function (b, a) {
        var numA = parseInt(a.replace('OPE-', ''), 10);
        var numB = parseInt(b.replace('OPE-', ''), 10);
        
        return numB - numA;
    },

    "person-desc": function(a, b) {
        let numA = parseInt(a.replace("@", "99999"), 10);
        let numB = parseInt(b.replace("@", "99999"), 10);

        return numB - numA;
    },

    "person-asc": function(b, a) {
        let numA = parseInt(a.replace("@", "99999"), 10);
        let numB = parseInt(b.replace("@", "99999"), 10);

        return numB - numA;
    },

    "amount-desc": function(a, b) {
        var numA = parseFloat(a.replace('€', ''), 10);
        var numB = parseFloat(b.replace('€', ''), 10);

        return numB - numA;
    },

    "amount-asc": function(b, a) {
        var numA = parseFloat(a.replace('€', ''), 10);
        var numB = parseFloat(b.replace('€', ''), 10);

        return numB - numA;
    },

    "frdatetime-desc": function(a, b) {
        return convertFrDatetime(b).getTime() - convertFrDatetime(a).getTime();
    },

    "frdatetime-asc": function(b, a) {
        return convertFrDatetime(b).getTime() - convertFrDatetime(a).getTime();
    },

    "frdate-desc": function(a, b) {
        return convertFrDate(b).getTime() - convertFrDate(a).getTime();
    },

    "frdate-asc": function(b, a) {
        return convertFrDate(b).getTime() - convertFrDate(a).getTime();
    },
});