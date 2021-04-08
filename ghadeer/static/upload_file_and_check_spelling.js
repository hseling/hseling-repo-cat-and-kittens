var setupUploadFileAndCheckSpelling = function() {
    $('#docx-file').change(function() {
        console.log("#docx-file changed")
        $('#docx-form').ajaxSubmit({
            method: 'post',
            type: 'post',
            url: '/upload_file',
            success: function(data) {
                // После загрузки файла очистим форму.
                console.log(data);
                let file_id = data.file_id;
                //Запрашиваем данные об орфографических ошибках
                $.get(`/get_spelling_problems/${file_id}`, function(data) {
                    console.log(data.spelling_problems);
                    let spelling_problems = data.spelling_problems;
                    if (Array.isArray(spelling_problems) && spelling_problems.length > 0) {
                        //Создаем радиокнопки для вариантов исправления, по умолчанию выбран вариант "не исправлять"
                        spelling_problems.forEach(function(problem, problemId) {
                            var formattedText = problem.context;
                            var correctionOptions = problem.s;
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
                                var chosen_value = $(`input[name=${problemId}]:checked`).val();
                                problem['chosen_value'] = chosen_value;
                            });

                            //И отправляем на сервер для внесения исправлений
                            $.ajax({
                                type: "POST",
                                url: "/correct_spelling",
                                dataType: "json",
                                contentType: "application/json; charset=utf-8",
                                data: JSON.stringify({
                                    'file_id': file_id,
                                    'problems_with_corrections': spelling_problems
                                }),
                                //В случае успеха идем на страницу правок
                                success: function() {
                                    console.log('success');
                                    window.location.replace(encodeURI(`/analysis?file_id=${file_id}`));
                                }
                            })
                            //добавить случай неуспеха
                        });
                        //Если ошибок не было, сразу идем
                    } else {
                        window.location.replace(
                            encodeURI(`/analysis?file_id=${file_id}`)
                        );
                    }
                })
            },
            //Если с сервера пришло сообщение о том, что файл некорректный, выводим его
            error: function(error) {
                console.error("upload_file@error:", error);
                const errorText = getErrorText(error);
                $('#upload_instruction').text(errorText);
            }
        });
    });
}


var getErrorText = function(error) {
    if (error.status >= 500) {
        return `Произошла серверная ошибка. Вы ничего по этому поводу сделать не сможете. Вот и печальтесь теперь.`;
    }

    return `Ошибка: ${error.responseText}. Исправьте и повторите попытку`;
}

setTimeout(setupUploadFileAndCheckSpelling, 0);