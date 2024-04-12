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
})