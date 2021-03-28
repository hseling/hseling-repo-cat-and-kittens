function formatProblemContext(problem){
    const context = problem.context;
    let formattedContext = context;
    if (typeof context === "string" &&
        typeof problem.context_pos === "number" &&
        typeof problem.context_end === "number" &&
        problem.context_pos >= 0 &&
        problem.context_pos < context.length-1 &&
        problem.context_end > 0 &&
        problem.context_end <= context.length-1
    ){
        const pretext = context.slice(0, problem.context_pos);
        const problemText = context.slice(problem.context_pos, problem.context_end);
        const posttext = context.slice(problem.context_end);
        formattedContext = pretext+'<b>'+problemText+'<\b>'+posttext;
    }
    return formattedContext
}


//$("input[name='submit_checking']").bind('click', function() {
//    const editedText = $('.edited_text_field').val();
//   const file_id = urlParams.get('file_id');

var setupUploadFileAndCheckSpelling = function() {
    $('.upload_text').on('change keyup keydown paste cut', 'textarea', function() {
        console.log('update edited text');
        $(this).height(0).height(this.scrollHeight);
      }).find('textarea').change();
      $("input[name='submit_text']").bind('click', function() {
          const text = $('#user_text_field').val();
            $.ajax({
                type: "POST",
                url: "/web/upload_text_old",
                dataType: "json",
                contentType: "application/json; charset=utf-8",
                data: JSON.stringify({
                  'text': text
                }),
                success: function(data){
                    const file_id = data.file_id;
                    $.get(`/web/get_spelling_problems/${file_id}`, function(data){
                        const spelling_problems = data.spelling_problems;
                        if (Array.isArray(spelling_problems) && spelling_problems.length > 0) {
                            //Создаем радиокнопки для вариантов исправления, по умолчанию выбран вариант "не исправлять"
                            spelling_problems.forEach(function(problem, problemId) {
                                const formattedText = formatProblemContext(problem);
                                const correctionOptions = problem.s;
                                problemHtml = `<legend>${formattedText}</legend>`;
                                problemHtml += `
                                <div class="mb-3 form-check-inline">
                                  <input class="form-check-input" type="radio" id="radio_${problemId}_none" name=${problemId} value="не исправлять" checked="checked">
                                  <label class="form-check-label" for="radio_${problemId}_none">не исправлять</label>
                                </div>`;

                                correctionOptions.forEach(function(option, optionIndex) {
                                    const optionId = `radio_${problemId}_${optionIndex}`
                                    problemHtml += `
                                      <div class="mb-3 form-check-inline">
                                        <input class="form-check-input" type="radio" id=${optionId} name=${problemId} value=${option}>
                                        <label class="form-check-label" for=${optionId}>${option}</label>
                                      </div>`;
                                });
                                $('.spelling_options').append(problemHtml);
                            });
                            //При нажатии на кнопку отправки орфографии собираем выбранные варианты
                            $("input[name='submit_spelling']").bind('click', function() {
                                spelling_problems.forEach(function(problem, problemId) {
                                    const chosen_value = $(`input[name=${problemId}]:checked`).val();
                                    problem['chosen_value'] = chosen_value;
                                });

                                //И отправляем на сервер для внесения исправлений
                                $.ajax({
                                    type: "POST",
                                    url: "web/correct_spelling",
                                    dataType: "json",
                                    contentType: "application/json; charset=utf-8",
                                    data: JSON.stringify({
                                        'file_id': file_id,
                                        'problems_with_corrections': spelling_problems
                                    }),
                                    //В случае успеха идем на страницу правок
                                    success: function() {
                                        console.log('success');
                                        window.location.replace(encodeURI(`/web/analysis?file_id=${file_id}`));
                                    }
                                })
                            })
                        } else {
                            window.location.replace(encodeURI(`/web/analysis?file_id=${file_id}`));
                        }
                    })
                },
                error:  function(error) {
                    console.error("upload_file@error:", error);
                    const errorText = getErrorText(error);
                    $('#upload_instruction').text(errorText);
                }
            });
        });
    }

//     //Если с сервера пришло сообщение о том, что текст некорректный, выводим его
//     error: function(error) {
//         console.error("upload_file@error:", error);
//         const errorText = getErrorText(error);
//         $('#upload_instruction').text(errorText);
//         }
//         });
//     });
// }



// var setupUploadFileAndCheckSpelling = function() {
//     $('.upload_text').on('change keyup keydown paste cut', 'textarea', function() {
//         console.log('update edited text');
//         $(this).height(0).height(this.scrollHeight);
//       }).find('textarea').change();

//     $('#docx-file').change(function() {
//         console.log("#docx-file changed")
//         $('#docx-form').ajaxSubmit({
//             method: 'post',
//             type: 'post',
//             url: 'upload_file',
//             success: function(data) {
//                 // После загрузки файла очистим форму.
//                 console.log(data);
//                 let file_id = data.file_id;
//                 //Запрашиваем данные об орфографических ошибках
//                 $.get(`get_spelling_problems/${file_id}`, function(data) {
//                     console.log(data.spelling_problems);
//                     let spelling_problems = data.spelling_problems;
//                     if (Array.isArray(spelling_problems) && spelling_problems.length > 0) {
//                         //Создаем радиокнопки для вариантов исправления, по умолчанию выбран вариант "не исправлять"
//                         spelling_problems.forEach(function(problem, problemId) {
//                             var formattedText = formatProblemContext(problem);
//                             var correctionOptions = problem.s;
//                             problemHtml = `<legend>${formattedText}</legend>`;
//                             problemHtml += `
//                         <div class="mb-3 form-check-inline">
//                                 <input class="form-check-input" type="radio" id="radio_${problemId}_none" name=${problemId} value="не исправлять" checked="checked">
//                                 <label class="form-check-label" for="radio_${problemId}_none">не исправлять</label>
//                         </div>`;

//                             correctionOptions.forEach(function(option, optionIndex) {
//                                 const optionId = `radio_${problemId}_${optionIndex}`
//                                 problemHtml += `
//                                     <div class="mb-3 form-check-inline">
//                                         <input class="form-check-input" type="radio" id=${optionId} name=${problemId} value=${option}>
//                                         <label class="form-check-label" for=${optionId}>${option}</label>
//                                     </div>`;
//                             });
//                             $('.spelling_options').append(problemHtml);
//                         });
//                         //При нажатии на кнопку отправки орфографии собираем выбранные варианты
//                         $("input[name='submit_spelling']").bind('click', function() {
//                             spelling_problems.forEach(function(problem, problemId) {
//                                 var chosen_value = $(`input[name=${problemId}]:checked`).val();
//                                 problem['chosen_value'] = chosen_value;
//                             });

//                             //И отправляем на сервер для внесения исправлений
//                             $.ajax({
//                                 type: "POST",
//                                 url: "correct_spelling",
//                                 dataType: "json",
//                                 contentType: "application/json; charset=utf-8",
//                                 data: JSON.stringify({
//                                     'file_id': file_id,
//                                     'problems_with_corrections': spelling_problems
//                                 }),
//                                 //В случае успеха идем на страницу правок
//                                 success: function() {
//                                     console.log('success');
//                                     window.location.replace(encodeURI(`/analysis?file_id=${file_id}`));
//                                 }
//                             })
//                             //добавить случай неуспеха
//                         });
//                         //Если ошибок не было, сразу идем
//                     } else {
//                         window.location.replace(
//                             encodeURI(`analysis?file_id=${file_id}`)
//                         );
//                     }
//                 })
//             },
//             //Если с сервера пришло сообщение о том, что текст некорректный, выводим его
//             error: function(error) {
//                 console.error("upload_file@error:", error);
//                 const errorText = getErrorText(error);
//                 $('#upload_instruction').text(errorText);
//             }
//         });
//     });
// }


var getErrorText = function(error) {
    if (error.status >= 500) {
        return `Произошла серверная ошибка. Вы ничего по этому поводу сделать не сможете. Вот и печальтесь теперь.`;
    }

    return `Ошибка: ${error.responseText}. Исправьте и повторите попытку`;
}

setTimeout(setupUploadFileAndCheckSpelling, 0);
