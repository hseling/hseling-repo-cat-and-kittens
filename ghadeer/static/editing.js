var possibleAspects;
var setupTextEditing = function() {
  var urlParams = new URLSearchParams(window.location.search);
  $('.edited_text').on('change keyup keydown paste cut', 'textarea', function() {
    console.log('update edited text');
    $(this).height(0).height(this.scrollHeight);
  }).find('textarea').change();

  $(window).on('resize', function() {
    $('textarea').change()
  });


  $('a[data-toggle="tab"]').on('shown.bs.tab', function(e) {
    console.log('nav-link clicked')
    $('textarea').change()
  })

  // $(".nav-link[name='editing-link']").bind('click', function() {
  //   console.log('nav-link clicked')
  //   $('textarea').change()
  // });


  $.get(`/send_last_version/${urlParams.get('file_id')}`, function(data) {
    const text = data.text;
    console.log('get_text', data);
    $(".source_text").html(text);
    $('.edited_text_field').val(text);
  });



  $.get(`/possible_aspects`, function(data) {
    console.log(data);
    let checkingOptionsDiv = document.getElementById("checking_options");
    possibleAspects = data.possible_aspects;
    //Добавить получение языка + английский в данных, если будем делать перевод
    let language = "russian";
    // <div class="mb-3 form-check">
    //   <input type="checkbox" class="form-check-input" id="exampleCheck1">te
    //   <label class="form-check-label" for="exampleCheck1">Check me out</label>
    // </div>
    possibleAspects.forEach(function(possibleAspect, aspectId) {
      const checkboxDiv = document.createElement("div");
      checkboxDiv.setAttribute("class", "mb-3 form-check");

      const checkbox = document.createElement("input");
      checkbox.setAttribute("type", "checkbox");
      checkbox.setAttribute("class", "nextCheckingAspectCheckbox form-check-input");

      const checkboxId = `nextCheckingAspectCheckbox_${aspectId}`
      checkbox.setAttribute("id", checkboxId);
      checkbox.setAttribute("value", possibleAspect.id);
      checkbox.checked = false;
      checkboxDiv.appendChild(checkbox);

      const checkboxLabel = document.createElement("label");
      checkboxLabel.setAttribute("class", "form-check-label");
      const labelText = possibleAspect[language] ? possibleAspect[language] : possibleAspect.id;
      checkboxLabel.innerHTML = `<strong class="aspect${aspectId+1}">${labelText}</strong><br>`;
      checkboxLabel.setAttribute("for", checkboxId);
      checkboxDiv.appendChild(checkboxLabel);

      checkingOptionsDiv.appendChild(checkboxDiv);
    });
  });

  $("input[name='submit_checking']").bind('click', function() {
      const editedText = $('.edited_text_field').val();
      const file_id = urlParams.get('file_id');
      //   const editedText4NextChecking = {
      //      'file_id': file_id,
      //     'text': editedText,
      //     'chosen_aspects': chosenNextCheckAspects;
      //   }
      $.ajax({
          type: "POST",
          //НАПИСАТЬ РУТ ДЛЯ СОХРАНЕНИЯ
          url: "/save_edited_text",
          dataType: "json",
          contentType: "application/json; charset=utf-8",
          data: JSON.stringify({
            'text': editedText,
            'file_id': file_id
          }),
          success: function() {
            console.log('success save_edited_text');
            let chosenNextCheckAspects = [];
            $('input.nextCheckingAspectCheckbox').each(function() {
              if ($(this).prop('checked')) {
                chosenNextCheckAspects.push(this.value);
              }
            });
            console.log('chosenNextCheckAspects', chosenNextCheckAspects)
            $.ajax({
              type: "POST",
              url: "/aspects_checking",
              dataType: "json",
              contentType: "application/json; charset=utf-8",
              data: JSON.stringify({
                'file_id': urlParams.get('file_id'),
                'chosen_aspects': chosenNextCheckAspects || []
              }),
              success: function(data) {
                console.log('success aspects_checking');
                const problems = data.problems;
                const text = data.text;
                const possibleAspectIds = possibleAspects.map(aspect => aspect.id)
                console.time('getCorrectionsHtml');
                const highlightedText = getCorrectionsHtml(text, problems, possibleAspectIds);
                console.timeEnd('getCorrectionsHtml');
               // console.log('highlightedText', highlightedText);
                $(".source_text").html(highlightedText);
                $('.edited_text textarea').val(text);
              }
              //window.location.replace(encodeURI(`/editing_form?text_id=${file_id}_spelling`));
            });
            //добавить случай неуспеха                   
          }
      });
  });

}

setTimeout(setupTextEditing, 0);