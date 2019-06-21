from django.shortcuts import render
from .misc_english import RHYME_LIST
from .forms import PostForm
import random
from collections import defaultdict, Counter
import re
import time

from gensim.models.doc2vec import Doc2Vec, TaggedDocument
import numpy as np
import argparse
import os
import pickle
import pexpect

os.environ['CUDA_VISIBLE_DEVICES'] = "2"

cmd = ['t2t-decoder',
       '--t2t_usr_dir=/tmp2/Laurice/transformer/custom_t2t/script',
       '--problem=lyrics',
       '--data_dir=/tmp2/Laurice/transformer/custom_t2t/self_english',
       '--model=transformer',
       '--hparams_set=transformer_base_single_gpu',
       '--output_dir=/tmp2/Laurice/transformer/custom_t2t/train_english',
       '--decode_interactive',
       '--worker_gpu_memory_fraction=0.1']


# run t2t-decoder as child process
child = pexpect.spawn(' '.join(cmd), encoding='utf-8')

# expect the '>' token of t2t-decoder output
# not a good method, but I haven't thought of a better way to read multi-line output from child.
child.expect('\n>', timeout=200)

with open('/tmp2/Laurice/transformer/Lyrics_demo/pos_table.pkl', 'rb') as f:
    POS_LEN_TABLE = pickle.load(f)

def generate_sentence(input_sentence):
    print ('[generate_sentence] input_sentence:', input_sentence)
    child.sendline(input_sentence)
    child.expect(['\n>', pexpect.EOF, pexpect.TIMEOUT])
    output = re.search(r'INFO.*\n', child.before) # parse output
    print('output:', output)
    if output:
        sentence_generated = output.group().split(':')[-1]
        sentence_generated = sentence_generated.strip().replace('SOS ', '').replace(' EOS', '')
        return sentence_generated

'''
# doc2vec method
def gen_first_sentence(keywords=None):
    data_path = '/tmp2/Laurice/transformer/Lyrics_demo/demo_site/lyrics/d2v/lyrics.txt'
    model_path = '/tmp2/Laurice/transformer/Lyrics_demo/demo_site/lyrics/d2v/my_doc2vec_model'

    with open(data_path, 'r') as f:
        documents = [TaggedDocument(doc, [i]) for i, doc in enumerate(f)]

    model = Doc2Vec.load(model_path)

    if keywords is not None and isinstance(keywords, str):
        # get the sentence with highest prob.
        vec = model.infer_vector(keywords.strip())
        sims = model.docvecs.most_similar([vec], topn=1)
        return documents[sims[0]]
    else:
        # get a random sentence from documents
        rand_id = random.randint(0, len(documents)-1)
        return documents[rand_id][0]
'''

# word match method
def gen_first_sentence(keywords):
    lyrics_path = '/tmp2/Laurice/transformer/Lyrics_demo/demo_site/lyrics/data/lyrics_char.txt'
    with open(lyrics_path, 'r') as f:
        lyrics = f.read().replace(' ', '')
        lyric_lines = lyrics.splitlines()
    if keywords == None:
        keywords = []
    else:
        keywords = ''.join(keywords)

    ngram = len(keywords)
    match = []
    while ngram > 0:
        if len(match) > 0:
            break
        start = 0
        while start+ngram <= len(keywords):
            word = keywords[start: start+ngram]
            match += re.findall(r'.*'+word+'.*\n', lyrics)
            start += 1
        ngram -= 1

    if len(match) == 0:
        rand_id = random.randint(0, len(lyric_lines)-1)
        return lyric_lines[rand_id]
    else:
        counter = Counter(match)
        return counter.most_common(1)[0][0].strip()

def isLegalSentence(original_input_sentence, sentence_now):
    if sentence_now == None:
        return False
    input_lyric = ['SOS'] + original_input_sentence.split() + ['EOS']
    input_lyric_bigrams = [tuple(input_lyric[i:i+2]) for i in range(len(input_lyric)-2)]
    output_lyric = ['SOS'] + sentence_now.split() + ['EOS']
    output_lyric_bigrams = [tuple(output_lyric[i:i+2]) for i in range(len(output_lyric)-2)]
    print('input_bigram', input_lyric_bigrams)
    print('output_bigram', output_lyric_bigrams)
    # same bigram should not appear over 2 times in a sentence
    print('output_counter', Counter(output_lyric_bigrams).most_common(5))
    print('total_counter', Counter(output_lyric_bigrams + input_lyric_bigrams).most_common(5))
    head_tail_limit = 4
    if len(input_lyric) > head_tail_limit and len(output_lyric) > head_tail_limit:
        if input_lyric[:head_tail_limit] == output_lyric[:head_tail_limit]:
            return False
        if input_lyric[-head_tail_limit:] == output_lyric[-head_tail_limit:]:
            return False
    if Counter(output_lyric_bigrams).most_common(1)[0][1] > 2:
        return False
    if Counter(input_lyric_bigrams + output_lyric_bigrams).most_common(1)[0][1] > 3:
        return False
    if len(set(input_lyric_bigrams) & set(output_lyric_bigrams)) / len(set(output_lyric_bigrams)) > 0.3:
        return False
    
    return True

def gen_model_input(rhyme, keywords, hidden_sentence, length, pattern, selected_index, length_word):
    # basic test, should be removed.
    # tmp = generate_sentence('SOS 好 難 搞 EOS 3 1 還 2 真 3 的 || || u || 6')
    # 我現在才認真看你的範例句哈哈哈哈，笑死我了XDDD
    # print(tmp)
    # return [], []


    # rhyme is already done
    line_count = 6
    zero_sentence = keywords
    # Need to decide how many lines first
    if (pattern == '0' or pattern == '1') and hidden_sentence != None:
        line_count = len(hidden_sentence)
    elif length != None:
        line_count = len(length)
        
    #zero_sentence = gen_first_sentence(keywords).strip()
    # if no keyword then random generate a sentence
    #zero_sentence = ' '.join(zero_sentence.replace(' ', ''))
    # Use pattern to decide the condition of each sentence
    # length of each sentence is decided in this section
    ch_position = []
    ch_position_num = []
    # selected_index 0_0 1_0 1_1 need to plus one for col index
    selected_index = selected_index.strip().split(' ')
    selected_index = [ind.split('_') for ind in selected_index]
    index_word_bind = list(zip(selected_index, hidden_sentence))
    selected_position = defaultdict(list)
    for index, word in index_word_bind:
        row, col = index
        selected_position[int(row)].append((int(col)+1, word))
    ch_count = 0
    for i in range(len(length)):
        ch_row = []
        ch_row_num = []
        col_word_now = sorted(selected_position[i], key=lambda x: x[0]) if i in selected_position else None
        if col_word_now:
            for col, word in col_word_now:
                ch_row.append((col, word))
                ch_row_num.append(col)
                ch_count += 1
        ch_position.append(ch_row)
        ch_position_num.append(ch_row_num)

    # ch_position = [[row0], [row1], ....]; rhyme = 'u'; length = [11, 12, 13]; hidden_sentence = '你好'
    # generate first sentence if there's zero sentence
    generated_lyrics = []
    input_sentence = ''
    sentence_now = ''
    for row_num, length_row in enumerate(length):
        print('row_num:', row_num)
        if row_num == 0:
            condition_count = 0
            if len(ch_position[row_num]) != 0:
                condition = ''
                for c, p in ch_position[row_num]:
                    condition = condition + str(c) + ' ' + p + ' '
                    condition_count += 1
                condition = str(condition_count) + ' ' + condition
            else:
                condition = '0 '
            
            if row_num < len(length_word):
                length_word_row = ' '.join(length_word[row_num].split(';'))
            else:
                length_word_row = ''

            input_sentence = 'SOS ' + zero_sentence + ' EOS ' + condition + '|| || ' + \
                             rhyme + ' || ' + length_word_row + ' || ' + str(length_row)
            #SOS 心 疼 你 还 没 挣 脱 思 念 的 囚 禁 EOS 2 11 后 1 他 || r p r m m v v v v f f d v v || u || 14,SOS 他 在 你 一 段 难 忘 远 行 最 后 却 离 去 EOS
            # TODO
            # model need to be called by here
            sentence_now = generate_sentence(input_sentence)
            sentence_now = sentence_now.strip('<EOS>')
        else:
            '''
            illegal = True
            padded_sentence_index = row_num
            print("="*80)
            original_input_sentence = input_sentence
            retry_count = 0
            pos_string = ''
            while illegal and padded_sentence_index >= 0:
                condition_count = 0
            '''
            if len(ch_position[row_num]) != 0:
                condition = ''
                for c, p in ch_position[row_num]:
                    condition = condition + str(c) + ' ' + p + ' '
                    condition_count += 1
                condition = str(condition_count) + ' ' + condition
            else:
                condition = ''

            if row_num < len(length_word):
                length_word_row = ' '.join(length_word[row_num].split(';'))
            else:
                length_word_row = ''

            new_input_sentence = 'SOS ' + input_sentence + ' EOS ' + condition + '|| ' +\
                                 rhyme + ' || ' + length_word_row + ' || ' + str(length_row)
            # TODO
            # model need to be called by here
            sentence_now = generate_sentence(new_input_sentence)
            sentence_now = sentence_now.strip('<EOS>')
            print('sentence_now', sentence_now)
            print('row_num', row_num)
                
            '''
                if not isLegalSentence(original_input_sentence, sentence_now):
                    print("ILLEGAL!!!!!!!!!!!")
                    if (retry_count >= 5):
                        break
                    if retry_count < 2:
                        padded_sentence_index = min(padded_sentence_index, len(generated_lyrics)-1)
                        padded_sentence_index -= 1
                        if row_num == 1 or padded_sentence_index == -1:
                            input_sentence = zero_sentence + ' ' + input_sentence
                        else:
                            input_sentence = ' '.join(list(generated_lyrics[padded_sentence_index])) + ' ' + input_sentence
                    else:
                        input_sentence = original_input_sentence
                        try:
                            pos_string = random.choice(POS_LEN_TABLE[int(length_row)])
                            retry_count += 1
                        except:
                            ipdb.set_trace()
                            break
                else:
                    illegal = False
            '''
            print('input_sentence:', input_sentence)



        print ('sentence_now:', sentence_now)
        output_format = sentence_now.split(' ')
        
        generated_lyrics.append(output_format)
                                                       
        input_sentence = sentence_now
    return generated_lyrics, ch_position_num

# main page for lyrics demo
def lyrics(req):
    if req.method == 'POST':
        print(RHYME_LIST)
        form = PostForm(req.POST or None)
        if form.is_valid():
            rhyme = form.cleaned_data['rhyme']
            keywords = form.cleaned_data['keywords'].replace(',', '').replace('.', '')
            hidden_sentence = form.cleaned_data['hidden_sentence'].strip().split()
            if form.cleaned_data['length'].strip() == '':
                form.cleaned_data['length'] = ';'.join(['10']*len(hidden_sentence))
            length = form.cleaned_data['length']
            length_word = form.cleaned_data['length_word']
            print(length)
            print('length_word: ', length_word)
            
            pattern = form.cleaned_data['pattern']
        if int(rhyme) == 0:   # random a rhyme if not given
            rhyme = random.choice(RHYME_LIST[1:])[1].split(' ')[0]
        else:
            rhyme = RHYME_LIST[int(rhyme)][1].split(' ')[0]
        
        if keywords.strip() == '':
            keywords = ' '.join(hidden_sentence)

        print('selected', req.POST['selected_index'])
        selected_index = req.POST['selected_index']
        print('keywords:', keywords)

        if length.strip() == '':
            length = [10] * len(hidden_sentence)
        else:
            length = re.sub('[^0-9;]','', length)
            length = length.strip(';').split(';')
        if length_word.strip() != '':
            length_word = re.sub('[^0-9;|]','', length_word)
            length_word = length_word.strip('||').split('||')
        print(length)
        print(hidden_sentence)


        model_output, ch_position_num = gen_model_input(rhyme, keywords,\
                                                        hidden_sentence, length,\
                                                        pattern, selected_index, length_word)

        generated_lyrics = list(zip(model_output, ch_position_num))

        print (generated_lyrics)

        return render(req, 'index.html', {'generated_lyrics': generated_lyrics,
                                          'rhyme'           : rhyme,
                                          'hidden_sentence' : hidden_sentence,
                                          'form'            : form,
                                          'selected_index'  : selected_index})

    elif req.method == 'GET':
        form = PostForm()
        #generate_sentence('SOS 夜 空 真 美 EOS 1 1 你 || || u || 5')
        #child.expect(['\n>', pexpect.EOF, pexpect.TIMEOUT])
        return render(req, 'index.html', {'form': form})


