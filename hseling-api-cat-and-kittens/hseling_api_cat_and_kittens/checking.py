from hseling_api_cat_and_kittens.morphology_check import *
from hseling_lib_cat_and_kittens.syntax import *
from hseling_lib_cat_and_kittens.duplicates import check_duplicates
from abc import ABC, abstractmethod
from hseling_lib_cat_and_kittens import parsing


class AbstractAspectChecker:
    @property
    @abstractmethod
    def input_type(self):
        pass

    @abstractmethod
    def check(self, data):
        pass

class GenetiveChainsChecker(AbstractAspectChecker):
    input_type = 'connlu_tokenlists'

    def check(self, tokenlists):
        return find_genitive_chaines(tokenlists)

class ComparativeChecker(AbstractAspectChecker):
    input_type = 'connlu_tokenlists'

    def check(self, tokenlists):
        return find_wrong_comparativ(tokenlists)

class IvsWeChecker(AbstractAspectChecker):
    input_type = 'connlu_tokenlists'

    def check(self, tokenlists):
        return find_IvsWe_problems(tokenlists)

class MorphologyChecker(AbstractAspectChecker):
   input_type = 'connlu_tokenlists'

   def check(self, tokenlists):
      return correction(tokenlists)

class DuplicatesChecker(AbstractAspectChecker):
    input_type = 'text'

    def check(self, text):
        return check_duplicates(text)


ASPECT2CHECKER  = {
    'morphology': MorphologyChecker(),
    'duplicates': DuplicatesChecker(),
    'genetive_chains': GenetiveChainsChecker(),
    'comparatives':ComparativeChecker(),
    'IvsWe': IvsWeChecker()
}

def check_text(text, aspects):
    checking_results = {}
    parsed_text = None
    for aspect in aspects:
        checker = ASPECT2CHECKER[aspect]
        if checker.input_type == 'connlu_tokenlists':
            if parsed_text == None:
                parsed_text = parsing.make_conll_with_udpipe(text)
            checking_results[aspect] = checker.check(parsed_text)
        elif checker.input_type == 'text':
            checking_results[aspect] = checker.check(text)
        else:
            checking_results[aspect] = []
    return checking_results
