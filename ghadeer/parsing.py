from ufal.udpipe import Model, Pipeline, ProcessingError, InputFormat
import os
import re

def make_conll_with_udpipe(text):
    model_path = os.path.join(os.getcwd(), 'udparsers', 'russian-syntagrus-ud-2.5-191206.udpipe') # здесь указать путь к модели
    model = Model.load(model_path)
    pipeline = Pipeline(model, 'tokenizer=ranges', Pipeline.DEFAULT, Pipeline.DEFAULT, 'conllu')
    return pipeline.process(text)

def main():
    print('none')
if __name__ == "__main__":
    main()