from ufal.udpipe import Model, Pipeline
import os
import re
import conllu

MODELS_DIR = '/dependencies/hseling-lib-cat-and-kittens/models/'
MODEL_NAMES = {
    'russian': 'russian-syntagrus-ud-2.5-191206.udpipe'
}

def make_conll_with_udpipe(text):
    model_path = MODELS_DIR + MODEL_NAMES['russian']
    model = Model.load(model_path)
    pipeline = Pipeline(model, 'tokenizer=ranges', Pipeline.DEFAULT, Pipeline.DEFAULT, 'conllu')
    udpipe_output = pipeline.process(text)
    return conllu.parse(udpipe_output)

def get_token_start(token: conllu.models.Token):
    return int(token['misc']['TokenRange'].split(':')[0])

def get_token_end(token: conllu.models.Token):
    return int(tokem['misc']['TokenRange'].split(':')[1])

def main():
    print('none')

if __name__ == "__main__":
    main()
