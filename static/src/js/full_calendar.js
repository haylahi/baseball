$(document).ready(function () {
  $('.data_full_calendar_table').dataTable( {
    "oLanguage": {
      "sSearch": "Rechercher:", 
      "sZeroRecords": "Aucun match correspondant"
         },
    "bPaginate": false,
    "bLengthChange": false,
    "bFilter": true,
    "bSort": false,
    "bInfo": false,
    "bAutoWidth": false 
              } );
});


