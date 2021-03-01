var setupTextEditing = function() {
    var urlParams = new URLSearchParams(window.location.search);
    $.get(`/get_statistics/${urlParams.get('file_id')}`, function(data) {
        const readability = data.readability_score;
        $("#FKG").text(readability);

        const file_id = urlParams.get('file_id');
        $("#filename").text(file_id);
        
        const total = data.total_words;
        $("#totalWords").text(total);

        const unique = data.unique_words;
        $("#uniqueWords").text(unique);

        const CEFR = data.CEFR;
        $("#CEFR").text(CEFR);

        var barData = {
            labels: ['ECON', 'JUR', 'LING', 'PSYCH', 'HIST', 'SOC', 'YOU'],
            datasets: [{
                fillColor: ['rgba(151,187,205,0.2)', "rgba(151,187,205,0.2)", "rgba(151,187,205,0.2)", "rgba(151,187,205,0.2)", "rgba(151,187,205,0.2)", "rgba(151,187,205,0.2)", "rgba(151,187,205,1)"],
                strokeColor: "rgba(151,187,205,1)",
                pointColor: "rgba(151,187,205,1)",
                data : [6.91, 5.41, 6.06, 6.7, 4.84, 6.72, readability]
                }]
            }
        var mychart = document.getElementById("chart").getContext("2d");

        steps = 10
        max = 9

        new Chart(mychart).Bar(barData, {
        scaleOverride: true,
        scaleSteps: steps,
        scaleStepWidth: Math.ceil(max / steps),
        scaleStartValue: 0,
        scaleShowVerticalLines: true,
        scaleShowGridLines: true,
        barShowStroke: true,
        scaleShowLabels: true
        }
        );

    });

}

setTimeout(setupTextEditing, 0);