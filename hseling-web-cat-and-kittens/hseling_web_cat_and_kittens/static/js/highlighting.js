function addTags(text, labels) {    if (!labels) return text;
    const openingTags = [...labels]
        .map(function(label) {
            return `<strong class="${label}">`;
        })
        .join('');
    const closingTags = [...labels]
        .map(function(label) {
            return '</strong>';
        })
        .join('');
    return `${openingTags}${text}${closingTags}`;
}


function transformProblemsIntoDictionary(problems) {
    const id2labels = {};
    const problemTypes = Object.keys(problems)
    console.debug("transformProblemsIntoDictionary@problemTypes:", problemTypes)
    problemTypes.forEach(function(problemType) {
        const similarProblems = problems[problemType]

        similarProblems
            .filter(problem => {
                const isBosNumber = typeof problem.bos === 'number';
                if (!isBosNumber) console.error('bos is not a number', problem);

                const isEndNumber = typeof problem.end === 'number';
                if (!isEndNumber) console.error('end is not a number', problem);

                const isEndLargerThenBos = problem.end > problem.bos;
                if (!isEndLargerThenBos) console.error('end is not larger than bos', problem);

                const isValid = isBosNumber && isEndNumber && isEndLargerThenBos;

                return isValid
            })
            .forEach(problem => {
                console.debug("transformProblemsIntoDictionary > problem:", problem)
                for (let symbolIndex = problem.bos; symbolIndex < problem.end; symbolIndex++) {
                    if (!id2labels[symbolIndex]) {
                        id2labels[symbolIndex] = new Set();
                        //check 2 similar tags case
                    }
                    id2labels[symbolIndex].add(problemType);
                }
            })
    })
    console.debug("transformProblemsIntoDictionary@id2labels:", id2labels)
    return id2labels
}

function areSetsEqual(set1, set2) {
    if (!set1 && !set2) return true;
    if (typeof set1 !== typeof set2) return false;
    if (set1.size !== set2.size) return false;
    for (const item of set1)
        if (!set2.has(item)) return false;
    return true;
}

function highlightText(text, problems) {
    console.debug('highlightText@text.length:', text.length);
    console.debug('highlightText@problems:', problems);
    if (!text) {
        return '';
    }
    const id2labels = transformProblemsIntoDictionary(problems);

    const htmlParts2Highlight = [];
    let currentStartId = 0;
    let currentClassLabels = id2labels[currentStartId];
    for (let currentEndId = 1; currentEndId < text.length; currentEndId++) {
        if (!areSetsEqual(id2labels[currentEndId], currentClassLabels)) {
            const currentTextFragment = text.slice(currentStartId, currentEndId);

            const currentHtmlPart = addTags(currentTextFragment, currentClassLabels);
            console.debug('currentHtmlPart:', currentHtmlPart);
            console.debug('currentClassLabels:', currentClassLabels)
            htmlParts2Highlight.push(currentHtmlPart);
            currentStartId = currentEndId;
            currentClassLabels = id2labels[currentEndId];
        }
    }
    const lastTextFragment = text.slice(currentStartId);
    htmlParts2Highlight.push(addTags(lastTextFragment, currentClassLabels));

    return htmlParts2Highlight.join('');
}

var getCorrectionsHtml = function(text, corrections, possibleAspectIds) {
    console.log('getCorrectionsHtml', '@corrections', corrections, '@possibleAspectIds', possibleAspectIds)
    let class2corrections = {};
    possibleAspectIds.forEach(function(aspectId, aspectIndex) {
        //Если была запрошена проверка этого аспекта
        //Доделать: выводить сообщение, если нет ошибок
        if (corrections[aspectId] && corrections[aspectId].length > 0) {
            const aspectId2Show = aspectIndex + 1;
            correctionClass = `aspect${aspectId2Show}`;
            //Функция раскраски должна знать про классы, а не про содержательные индекcы
            class2corrections[correctionClass] = corrections[aspectId];
        }
    })
    return highlightText(text, class2corrections);
}