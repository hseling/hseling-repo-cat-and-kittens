var response = $("#response").data("db");
var displayType = $("#response").data("displaytype");
// String.prototype.replaceAll = function(search, replacement) {
//   var target = this;
//   return target.replace(new RegExp(search, 'g'), replacement);
// };

// const regexStart = /((?<=\s)\%{3}|^\%{3})/g
// const regexEnd = /(?<=\S)\%{3}/g
// const metaStart = /((?<=\s)\&{3}|^\%{3})/g
// const metaEnd = /(?<=\S)\&{3}/g

// Builds the HTML Table out of response.
function buildHtmlTable(selector) {
  var columns = addAllColumnHeaders(response, selector);
  var row$ = $('<tbody/>');
  for (var i = 0; i < response.length; i++) {
    row$.append($('<tr/>'));
    for (var colIndex = 0; colIndex < columns.length; colIndex++) {
      var cellValue = response[i][columns[colIndex]];
      // if (typeof cellValue === 'string') {
      //   cellValue = cellValue.replaceAll(regexStart, "<strong>");
      //   cellValue = cellValue.replaceAll(regexEnd, "</strong>");
      //   cellValue = cellValue.replaceAll(metaStart, "<p class='italics'>");
      //   cellValue = cellValue.replaceAll(metaEnd, "</p>")
      // }
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

function getColumnHeader(response, selector) {
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

  return columnSet[0];
}


function databaseExamples(selector) {
  var key = getColumnHeader(response, selector);
  var row$ = $('<tbody/>');
  for (var i = 0; i < response.length; i++) {
    row$.append($('<tr/>'));
    var cell$ = $('<td/>');

    var firstParagraph$ = $("<p/>").html(response[i][key][0]).addClass("first-par hidden-paragraph");
    cell$.append(firstParagraph$);
    var mainParagraph$ = $("<p/>").html(response[i][key][1]).addClass("visible-paragraph");
    cell$.append(mainParagraph$);
    var lastParagraph$ = $("<p/>").html(response[i][key][2]).addClass("last-par hidden-paragraph");
    cell$.append(lastParagraph$);
    var reference = $("<p/>").html(response[i][key][3]).addClass("italics");
    cell$.append(reference);
    var button = $('<input/>').attr({
      type: "button",
      value: '<-- ... -->'
    }).addClass("expand-button btn btn-light");
    cell$.append(button);

    row$.append(cell$);

  }
  $(selector).append(row$);
}

function displayResponse(selector) {
  if (displayType == "table") {

    buildHtmlTable(selector);

  } else {

    databaseExamples(selector);

  }
}

function addClickExpandButtons() {
  const expandButtons = document.querySelectorAll('.expand-button');
  expandButtons.forEach(item => {
    item.addEventListener('click', (event) => {
      const firstPar = event.target.parentNode.querySelector('.first-par');
      const lastPar = event.target.parentNode.querySelector('.last-par');
      firstPar.classList.toggle('hidden-paragraph');
      firstPar.classList.toggle('visible-paragraph');
      lastPar.classList.toggle('hidden-paragraph');
      lastPar.classList.toggle('visible-paragraph');
    })
  })
}

setTimeout(addClickExpandButtons, 1000);

var type = $(".link-to-new-search").data("page");

if (type == "collocations") {
  $(".link-to-search").attr("href", "{{ url_for('collocations') }}")
} else if (type == "search") {
  $(".link-to-search").attr("href", "{{ url_for('search') }}")
} else {
  $(".link-to-search").attr("href", "{{ url_for('index') }}")
}