from checking import morphology_checker, duplicates_checker

UPLOAD_FOLDER = 'student_texts'
ALLOWED_EXTENSIONS = {'txt'}
ASPECTS =  [{'id': 'morphology','russian': 'Словоформы, не представленные в CAT'},
           {'id': 'duplicates','russian': 'Повторы'}]
ASPECT2FUNCTION  = {

    'morphology': morphology_checker,
    'duplicates': duplicates_checker
}
