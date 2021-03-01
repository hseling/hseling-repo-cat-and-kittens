var response = $("#response-table").data("db");

// Builds the HTML Table out of response.
function buildHtmlTable(selector) {
    var columns = addAllColumnHeaders(response, selector);
    var row$ = $('<tbody/>');
  
    for (var i = 0; i < response.length; i++) {
      row$.append($('<tr/>'));
      for (var colIndex = 0; colIndex < columns.length; colIndex++) {
        var cellValue = response[i][columns[colIndex]];
        if (cellValue == null) cellValue = "";
        row$.append($('<td/>').html(cellValue));
      }
      $(selector).append(row$);
    }
  }
  
  // Adds a header row to the table and returns the set of columns.
  // Need to do union of keys from all records as some records may not contain
  // all records.
  function addAllColumnHeaders(response, selector) {
    var columnSet = [];
    var headerTr$ = $('<thead/>');
    headerTr$.append($('<tr/>'));
  
    for (var i = 0; i < response.length; i++) {
      var rowHash = response[i];
      for (var key in rowHash) {
        if ($.inArray(key, columnSet) == -1) {
          columnSet.push(key);
          headerTr$.append($('<th scope="col"/>').html(key));
        }
      }
    }
    $(selector).append(headerTr$);
  
    return columnSet;
  }