var whichLemma = 0;

function basicPopup() {
url = 'search_morph'
popupWindow = window.open(url,'popUpWindow','height=500,width=500,left=100,top=100,resizable=yes,scrollbars=yes,toolbar=yes,menubar=no,location=no,directories=no, status=yes');
	}

window.receiveFromChild = function(obj) {

    if (whichLemma == 1){
    txtarea = document.getElementById('morph1')}
    else if (whichLemma == 2){
    txtarea = document.getElementById('morph2')}
    txtarea.value = obj

};

function sendChoiceToParent(){
  var form = document.forms['choice'];
  var inputs = form.getElementsByTagName('input')
  var checked = [];
  for (var i = 0; i < inputs.length; i++) {
    if (inputs[i].type == 'checkbox' && inputs[i].checked) {
        checked.push(inputs[i].value);
      }
    }
  window.opener.receiveFromChild ( checked );
  this.close();
}