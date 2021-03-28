var response = $("#response-table").data("db");

String.prototype.replaceAll = function(search, replacement) {
  var target = this;
  return target.replace(new RegExp(search, 'g'), replacement);
};

const regex_start = /((?<=\s)\%{3}|^\%{3})/g
const regex_end = /(?<=\S)\%{3}/g

// Builds the HTML Table out of response.
function buildHtmlTable(selector) {
    var columns = addAllColumnHeaders(response, selector);
    var row$ = $('<tbody/>');
  
    for (var i = 0; i < response.length; i++) {
      row$.append($('<tr/>'));
      for (var colIndex = 0; colIndex < columns.length; colIndex++) {
        var cellValue = response[i][columns[colIndex]];
        if (typeof cellValue === 'string') {
          cellValue = cellValue.replaceAll(regex_start, "<strong>");
          cellValue = cellValue.replaceAll(regex_end, "</strong>");
        }
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

var type = $(".link-to-new-search").data("page");

if (type == "collocations") {
  $(".link-to-search").attr("href", "{{ url_for('collocations') }}")
} else if (type == "search") {
  $(".link-to-search").attr("href", "{{ url_for('search') }}")
} else {
  $(".link-to-search").attr("href", "{{ url_for('index') }}")
}