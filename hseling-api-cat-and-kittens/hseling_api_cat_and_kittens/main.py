import os
from base64 import b64decode, b64encode
from flask import Flask, jsonify, request
from logging import getLogger
import secrets



from hseling_api_cat_and_kittens import boilerplate, db_queries

from hseling_lib_cat_and_kittens.process import process_data, process_udpipe
from hseling_lib_cat_and_kittens.query import query_data
from hseling_api_cat_and_kittens import checking


app = Flask(__name__)
app.config['DEBUG'] = False
app.config['LOG_DIR'] = '/tmp/'
if os.environ.get('HSELING_API_CAT_AND_KITTENS_SETTINGS'):
    app.config.from_envvar('HSELING_API_CAT_AND_KITTENS_SETTINGS')

app.config['HSELING_API_ENDPOINT'] = os.environ.get('HSELING_API_ENDPOINT')
app.config['HSELING_RPC_ENDPOINT'] = os.environ.get('HSELING_RPC_ENDPOINT')

app.config.update(
    CELERY_BROKER_URL=boilerplate.CELERY_BROKER_URL,
    CELERY_RESULT_BACKEND=boilerplate.CELERY_RESULT_BACKEND
)
celery = boilerplate.make_celery(app)
UPLOAD_FOLDER = 'data/upload'

if not app.debug:
    import logging
    from logging.handlers import TimedRotatingFileHandler
    # https://docs.python.org/3.6/library/logging.handlers.html#timedrotatingfilehandler
    file_handler = TimedRotatingFileHandler(os.path.join(app.config['LOG_DIR'], 'hseling_api_cat_and_kittens.log'), 'midnight')
    file_handler.setLevel(logging.WARNING)
    file_handler.setFormatter(logging.Formatter('<%(asctime)s> <%(levelname)s> %(message)s'))
    app.logger.addHandler(file_handler)

log = getLogger(__name__)


ALLOWED_EXTENSIONS = ['txt']

MODELS_DIR = '/dependencies/hseling-lib-cat-and-kittens/models/'
MODEL_NAMES = {
    'russian': 'russian-syntagrus-ud-2.5-191206.udpipe'
}

def get_server_endpoint():
    HSELING_API_ENDPOINT = app.config.get('HSELING_API_ENDPOINT')

    return HSELING_API_ENDPOINT

def do_process_task(file_ids_list):
    files_to_process = boilerplate.list_files(recursive=True,
                                              prefix=boilerplate.UPLOAD_PREFIX)
    if file_ids_list:
        files_to_process = [boilerplate.UPLOAD_PREFIX + file_id
                            for file_id in file_ids_list
                            if (boilerplate.UPLOAD_PREFIX + file_id)
                            in files_to_process]
    data_to_process = {file_id[len(boilerplate.UPLOAD_PREFIX):]:
                       boilerplate.get_file(file_id)
                       for file_id in files_to_process}
    processed_file_ids = list()
    for processed_file_id, contents in process_data(data_to_process):
        processed_file_ids.append(
            boilerplate.add_processed_file(
                processed_file_id,
                contents,
                extension='txt'
            ))
    return processed_file_ids

@celery.task
def process_task(file_ids_list=None):
    return do_process_task(file_ids_list)

@celery.task
def parse_file(text):
    from ufal.udpipe import Model, Pipeline
    model_path = MODELS_DIR + MODEL_NAMES['russian']
    model = Model.load(model_path)
    pipeline = Pipeline(model, 'tokenizer=ranges', Pipeline.DEFAULT, Pipeline.DEFAULT, 'conllu')
    return process_udpipe(text, pipeline)


@app.route('/api/healthz')
def healthz():
    app.logger.info('Health checked')
    return jsonify({"status": "ok", "message": "hseling-api-cat-and-kittens"})

@app.route('/api/upload', methods=['GET', 'POST'])
def upload_endpoint():
    if request.method == 'POST':
        if 'file' not in request.files:
            return jsonify({"error": boilerplate.ERROR_NO_FILE_PART})
        upload_file = request.files['file']
        if upload_file.filename == '':
            return jsonify({"error": boilerplate.ERROR_NO_SELECTED_FILE})
        if upload_file and boilerplate.allowed_file(
                upload_file.filename,
                allowed_extensions=ALLOWED_EXTENSIONS):
            return jsonify(boilerplate.save_file(upload_file))
    return boilerplate.get_upload_form()

@app.route('/api/upload_file', methods=['GET', 'POST'])
def upload_file():
    contents = ''
    if request.method == 'POST':
        contents = request.values.get('input_text', '')
        if contents:
            with open('/data/upload/upload.txt', 'w') as f:
                f.write(contents)
    return jsonify({"status" : "ok"})

@app.route('/api/files/<path:file_id>')
def get_file_endpoint(file_id):
    if file_id in boilerplate.list_files(recursive=True):
        return boilerplate.get_file(file_id)
    return jsonify({'error': boilerplate.ERROR_NO_SUCH_FILE})

@app.route('/api/files')
def list_files_endpoint():
    return jsonify({'file_ids': boilerplate.list_files(recursive=True)})

def do_process(file_ids):
    file_ids_list = file_ids and file_ids.split(",")
    task = process_task.delay(file_ids_list)
    return {"task_id": str(task)}

@app.route('/api/process')
@app.route("/api/process/<file_ids>")
def process_endpoint(file_ids=None):
    return jsonify(do_process(file_ids))


def do_query(file_id, query_type):
    if not query_type:
        return {"error": boilerplate.ERROR_NO_QUERY_TYPE_SPECIFIED}
    processed_file_id = boilerplate.PROCESSED_PREFIX + file_id
    if processed_file_id in boilerplate.list_files(recursive=True):
        return {
            "result": query_data({
                processed_file_id: boilerplate.get_file(processed_file_id)
            }, query_type=query_type)
        }
    return {"error": boilerplate.ERROR_NO_SUCH_FILE}

@app.route("/api/query/<path:file_id>")
def query_endpoint(file_id):
    query_type = request.args.get('type')
    return jsonify(do_query(file_id, query_type))

@app.route("/api/status/<task_id>")
def status_endpoint(task_id):
    return jsonify(boilerplate.get_task_status(task_id))

def do_test_mysql():
    conn = boilerplate.get_mysql_connection()
    cur = conn.cursor()
    cur.execute("SELECT table_name, column_name FROM INFORMATION_SCHEMA.COLUMNS")
    schema = dict()
    for table_name, column_name in cur.fetchall():
        schema.setdefault(table_name.decode('utf-8'), []).append(column_name)
    return {"schema": schema}

@app.route("/api/test_mysql")
def test_mysql_endpoint():
    return jsonify(do_test_mysql())

def get_endpoints(ctx):
    def endpoint(name, description, active=True):
        return {
            "name": name,
            "description": description,
            "active": active
        }

    all_endpoints = [
        endpoint("root", boilerplate.ENDPOINT_ROOT),
        endpoint("scrap", boilerplate.ENDPOINT_SCRAP,
                 not ctx["restricted_mode"]),
        endpoint("upload", boilerplate.ENDPOINT_UPLOAD),
        endpoint("process", boilerplate.ENDPOINT_PROCESS),
        endpoint("query", boilerplate.ENDPOINT_QUERY),
        endpoint("status", boilerplate.ENDPOINT_STATUS)
    ]

    return {ep["name"]: ep for ep in all_endpoints if ep}

@app.route("/api/collocation_search")
def bigram_search_endpoint():
    token = request.args.get("token")
    metric = request.args.get("metric")
    domain = request.args.get("domain")
    return jsonify({"values": db_queries.collocation_search(token, metric, domain)})

@app.route("/api/single_token_search")
def single_token_search_endpoint():
    token = request.args.get("token")
    domain = request.args.get("domain")
    return jsonify({"values": db_queries.single_token_search(token, domain)})

@app.route("/api/lemma_search")
def lemma_search_endpoint():
    lemma1 = request.args.get("lemma1")
    lemma2 = request.args.get("lemma2")
    morph1 = request.args.get("morph1")
    morph2 = request.args.get("morph2")
    # syntrole = request.args.get("syntrole")
    min_ = request.args.get("min")
    max_ = request.args.get("max")
    domain = request.args.get("domain")
    return jsonify({"values": db_queries.lemma_search(lemma1, lemma2, morph1, morph2, min_, max_, domain)})


# @app.route('/api/udpipe', methods=['POST'])
# def udpify():
#     from ufal.udpipe import Model, Pipeline
#     model_path = MODELS_DIR + MODEL_NAMES['russian']
#     model = Model.load(model_path)
#     pipeline = Pipeline(model, 'tokenizer=ranges', Pipeline.DEFAULT, Pipeline.DEFAULT, 'conllu')
#     data = request.get_json()
#     text = data['text'] if 'text' in data else ''
#     if text != '':
#         udpipe_output = pipeline.process(text)
#         solution = conllu.parse(udpipe_output)
#     else:
#         udpipe_output = pipeline.process('')
#         solution = conllu.parse(udpipe_output)
#     return jsonify({'solution' : str(solution)})

def generate_file_id():
    return secrets.token_urlsafe(16)


@app.route("/api/upload_text_old", methods=['POST'])
def upload_text_old():
    text = request.values.get('text', '')
    file_id = generate_file_id()
    file_name = file_id + '.txt'
    with open(os.path.join(UPLOAD_FOLDER, file_name), 'w') as f:
        f.write(text)
    return jsonify({'file_id': file_id})


@app.route("/api/save_next_version_old", methods=['POST'])
def save_next_version_old():
    text = request.values.get('text', '')
    file_id = request.values.get('file_id', '')
    if text and file_id:
        file_name = file_id + '.txt'
        with open(os.path.join(UPLOAD_FOLDER, file_name), 'w') as f:
            f.write(text)
    return jsonify({'success':True})


@app.route("/api/get_last_version_old/<file_id>", methods=['GET'])
def get_last_version_old(file_id):
    file_name = str(file_id)+'.txt'
    try:
        with open(os.path.join(UPLOAD_FOLDER, file_name)) as f:
            text = f.read()
        print('Текст считан')
        return jsonify({'text': text})
    except IOError:
        print('Текст не считан')
        return 'Wrong id', 404


@app.route("/api/check_text", methods=['POST'])
def check_text():
    #data = request.get_json(force=True)
    text = request.values.get('text', '')
    aspects = request.values.get('aspects', '')
    aspects = aspects.split('&')
    print('aspects', aspects)
    #text = data['text'] if 'text' in data else ''
    #aspects = data['aspects'] if 'aspects' in data else None
    problems = checking.check_text(text, aspects)
    return jsonify({'problems': problems})


@app.route("/api/")
def main_endpoint():
    ctx = {"restricted_mode": boilerplate.RESTRICTED_MODE}
    return jsonify({"endpoints": get_endpoints(ctx)})




if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True, port=5000)


__all__ = [app, celery]
