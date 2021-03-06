var whichLemma = 0;

function basicPopup() {
  url = 'search_morph'
  popupWindow = window.open(url, 'popUpWindow', 'height=500,width=500,left=100,top=100,resizable=yes,scrollbars=yes,toolbar=yes,menubar=no,location=no,directories=no, status=yes');
}

window.receiveFromChild = function (obj) {

  if (whichLemma == 1) {
    txtarea = document.getElementById('morph1')
  } else if (whichLemma == 2) {
    txtarea = document.getElementById('morph2')
  }
  txtarea.value = obj

};

function sendChoiceToParent() {
  var form = document.forms['choice'];
  var inputs = form.getElementsByTagName('input')
  var checked = [];
  for (var i = 0; i < inputs.length; i++) {
    if (inputs[i].type == 'radio' && inputs[i].checked) {
      checked.push(inputs[i].value);
    }
  }
  window.opener.receiveFromChild(checked);
  this.close();
}


window.onload = function () {
  const selectCorpus = document.querySelector('.form-control')
  selectCorpus.addEventListener('change', (event) => {
    const hiddenInput1 = document.querySelector('.hidden-input1');
    const hiddentInput2 = document.querySelector('.hidden-input2');
    hiddenInput1.value = event.target.value;
    hiddentInput2.value = event.target.value;
  })
}
