from ufal.udpipe import Model, Pipeline, ProcessingError, InputFormat
import os
import re
import conllu

def make_conll_with_udpipe(text):
    model_path = os.path.join(os.getcwd(), 'udparsers', 'russian-syntagrus-ud-2.5-191206.udpipe') # здесь указать путь к модели
    model = Model.load(model_path)
    pipeline = Pipeline(model, 'tokenizer=ranges', Pipeline.DEFAULT, Pipeline.DEFAULT, 'conllu')
    udpipe_output =  pipeline.process(text)
    return conllu.parse(udpipe_output)

def get_token_start(token: conllu.models.Token):
    return int(token['misc']['TokenRange'].split(':')[0])

def get_token_end(token: conllu.models.Token):
    return int(tokem['misc']['TokenRange'].split(':')[1])

def main():
    print('none')
if __name__ == "__main__":
    main()