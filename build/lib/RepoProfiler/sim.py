import nltk
from collections import Counter
from nltk.util import ngrams
from crystalbleu import corpus_bleu
import code_bert_score

nltk.download('punkt')

def get_similiraityScores(buggy_code, fixed_code, k=10):
    #tokenise the code snippets
    tokens1 = nltk.word_tokenize(buggy_code)
    tokens2 = nltk.word_tokenize(fixed_code)


    tokenized_corpus=tokens1+tokens2
    # <tokenized_corpus> is a list of strings

    # Extract all n-grams of length 1-4
    all_ngrams = []
    for n in range(1, 5):
        all_ngrams.extend(list(ngrams(tokenized_corpus, n)))

    #Calculate frequencies of all n-grams
    frequencies = Counter(all_ngrams)
    trivially_shared_ngrams = dict(frequencies.most_common(k))

    #Put actual parameters in expected format, i.e., [], [[]], etc.
    reference=tokens1
    hypothesis=tokens2 #hypothesis is also called as candidate
    references=[reference]
    list_of_references=[references]
    list_of_hypotheses=[hypothesis]

    #cbleu=nltk.translate.bleu_score.corpus_bleu(list_of_references, list_of_hypotheses)
    sbleu=nltk.translate.bleu_score.sentence_bleu(references, hypothesis)
    crystalBLEU_score=corpus_bleu(list_of_references, list_of_hypotheses,ignoring=trivially_shared_ngrams) #crystalBLEU
    bert_score = code_bert_score.score(cands = [fixed_code], refs = [[buggy_code]], lang = 'python', no_punc=True, device = 'cpu')
    # print('BERT_SCORE:',bert_score)
    # print('NLTK_CORPUS_BLEU: {:.6f}'.format(crystalBLEU_score))
    # print('NLTK_SENTENCE_BLEU: {:.6f}'.format(sbleu))
    return crystalBLEU_score, sbleu, bert_score

if __name__ == "__main__":

    get_similiraityScores('sim.py', 'sim.py', 5)

