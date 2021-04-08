function getUrlVars()
{
    var vars = [], hash;
    var hashes = window.location.href.slice(window.location.href.indexOf('?') + 1).split('&');
    for(var i = 0; i < hashes.length; i++)
    {
        hash = hashes[i].split('=');
        vars.push(hash[0]);
        vars[hash[0]] = hash[1];
    }
    return vars;
}

$(function () {
  var vars = getUrlVars(),
      task_id = vars["task_id"];

  if(task_id) {
    var check_parent = document.body;
    var textbox = document.getElementById("check2");
    check_parent.removeChild(textbox);
    var loader_div = document.createElement("div");
    loader_div.setAttribute('class','check-cat');
    check_parent.appendChild(loader_div);
    var loader = document.createElement("div");
    loader.setAttribute('class','loader');
    loader_div.appendChild(loader);
    var loader_img = document.createElement("div");
    loader_img.setAttribute('class','cat');
    loader_img.innerHTML = document.getElementById('catImage').innerHTML;
    var loader_p = document.createElement("p");
    var loader_text = document.createTextNode("Котики мурлычут...");
    loader_p.appendChild(loader_text);
    loader_div.appendChild(loader_p);
    loader_div.appendChild(loader_img);
    var get_status = function () {

      $.get("status?task_id=" + task_id, function(data) {
        if (data.ready) {
          check_parent.removeChild(loader_div);
          var check_result = document.createElement("div");
          check_result.setAttribute('class','cat')
          check_result.innerHTML = data.result;
          check_parent.appendChild(check_result);
          var back_button = document.createElement('div');
          back_button.setAttribute('class', 'backButton');
          back_button.innerHTML = document.getElementById('backButton').innerHTML;
          check_parent.appendChild(back_button);
        } else {
          setTimeout(get_status, 500);
        }
      });
    };

    get_status();
  }
});