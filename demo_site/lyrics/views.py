from django.shortcuts import render
from .misc import RHYME_LIST
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
from opencc import OpenCC
from hanziconv import HanziConv

os.environ['CUDA_VISIBLE_DEVICES'] = "2"

cmd = ['t2t-decoder',
       '--t2t_usr_dir=/tmp2/Laurice/transformer/custom_t2t/script',
       '--problem=lyrics',
       '--data_dir=/tmp2/Laurice/transformer/custom_t2t/self_ch_pos_rhy_len',
       '--model=transformer',
       '--hparams_set=transformer_base_single_gpu',
       '--output_dir=/tmp2/Laurice/transformer/custom_t2t/train_ch_pos_rhy_len',
       '--decode_interactive',
       '--worker_gpu_memory_fraction=0.1']


# run t2t-decoder as child process
child = pexpect.spawn(' '.join(cmd), encoding='utf-8')

# expect the '>' token of t2t-decoder output
# not a good method, but I haven't thought of a better way to read multi-line output from child.
child.expect('\n>', timeout=200)

def generate_sentence(input_sentence):
    print (input_sentence)
    child.sendline(input_sentence)
    child.expect(['\n>', pexpect.EOF, pexpect.TIMEOUT])
    output = re.search(r'INFO.*SOS.*\n', child.before) # parse output
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
def gen_first_sentence(keywords=None):
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


def gen_model_input(rhyme, first_sentence, keywords, hid_sentence, length, pattern, selected_index):
    # basic test, should be removed.
    # tmp = generate_sentence('SOS 好 難 搞 EOS 3 1 還 2 真 3 的 || || u || 6')
    # 我現在才認真看你的範例句哈哈哈哈，笑死我了XDDD
    # print(tmp)
    # return [], []


    # rhyme is already done
    line_count = 6
    zero_sentence = None
    # Need to decide how many lines first
    hid_sentence = HanziConv.toSimplified(hid_sentence)
    if (pattern == '0' or pattern == '1') and hid_sentence != None:
        line_count = len(hid_sentence)
    elif length != None:
        line_count = len(length)
    if not first_sentence:
        #import ipdb; ipdb.set_trace()
        if keywords:
            keywords = HanziConv.toSimplified(keywords)
            keywords = keywords.strip().split(' ')
            
        zero_sentence = gen_first_sentence(keywords).strip()
        # if no keyword then random generate a sentence
        zero_sentence = ' '.join(zero_sentence.replace(' ', ''))
    else:
        first_sentence = ' '.join(HanziConv.toSimplified(first_sentence).strip())
    # Use pattern to decide the condition of each sentence
    # length of each sentence is decided in this section
    ch_position = []
    ch_position_num = []
    if pattern == '0': #first character of each sentence
        for ch in hid_sentence:
            ch_position.append([(1, ch)])
            ch_position_num.append([1])
    elif pattern == '1': #last character of each sentence
        if length:
            for position, ch in zip(length, hid_sentence):
                ch_position.append([(int(position), ch)])
                ch_position_num.append([int(position)])
        else:
            length = [random.randint(6, 16) for _ in range(len(hid_sentence))]
            for position, ch in zip(length, hid_sentence):
                ch_position.append([(int(position), ch)])
                ch_position_num.append([int(position)])
    elif pattern == '2':
        position = 1
        if length:
            for ch in hid_sentence:
                ch_position.append([(position, ch)])
                ch_position_num.append([position])
                position += 1
        else:
            length = [x+1+random.randint(2, 10) for x in range(len(hid_sentence))]
            for ch in hid_sentence:
                ch_position.append([(position, ch)])
                ch_position_num.append([position])
                position += 1
    elif pattern == '3':
        # selected_index 0_0 1_0 1_1 need to plus one for col index
        selected_index = selected_index.strip().split(' ')
        selected_index = [ind.split('_') for ind in selected_index]
        index_word_bind = list(zip(selected_index, hid_sentence))
        selected_position = defaultdict(list)
        for index, word in index_word_bind:
            row, col = index
            selected_position[int(row)].append((int(col)+1, word))
        if length:
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
        else:
            length = [15] * 6
            # 6 * 15
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

    # ch_position = [[row0], [row1], ....]; rhyme = 'u'; length = [11, 12, 13]; hid_sentence = '你好'
    # generate first sentence if there's zero sentence
    generated_lyrics = []
    input_sentence = ''
    sentence_now = ''
    for row_num, length_row in enumerate(length):
        if row_num == 0:
            if zero_sentence:
                condition_count = 0
                if len(ch_position[row_num]) != 0:
                    condition = ''
                    for c, p in ch_position[row_num]:
                        condition = condition + str(c) + ' ' + p + ' '
                        condition_count += 1
                    condition = str(condition_count) + ' ' + condition
                else:
                    condition = '0 '
                input_sentence = 'SOS ' + zero_sentence + ' EOS ' + condition + '|| || ' + \
                                 rhyme + ' || ' + str(length_row)
                #SOS 心 疼 你 还 没 挣 脱 思 念 的 囚 禁 EOS 2 11 后 1 他 || r p r m m v v v v f f d v v || u || 14,SOS 他 在 你 一 段 难 忘 远 行 最 后 却 离 去 EOS
                # TODO
                # model need to be called by here
                sentence_now = generate_sentence(input_sentence)
                #sentence_now = generate_sentence(input_sentence)
            else:
                sentence_now = first_sentence
        else:
            condition_count = 0
            if len(ch_position[row_num]) != 0:
                condition = ''
                for c, p in ch_position[row_num]:
                    condition = condition + str(c) + ' ' + p + ' '
                    condition_count += 1
                condition = str(condition_count) + ' ' + condition
            else:
                condition = '0 '
            input_sentence = 'SOS ' + input_sentence + ' EOS ' + condition + '|| || ' + \
                             rhyme + ' || ' + str(length_row)
            # TODO
            # model need to be called by here
            #if not zero_sentence and row_num == 1:
            #    sentence_now = generate_sentence(input_sentence)
            sentence_now = generate_sentence(input_sentence)
        #print (input_sentence)
        print (sentence_now)
        output_format = sentence_now.split(' ')
        #for position in ch_position[row_num]:
        #    try:
        #        output_format[position[0]-1] = position[1]
        #    except IndexError:
        #        print ('Generated sentence is defferent from the condition.')
        #        continue
        generated_lyrics.append(HanziConv.toTraditional(''.join(output_format)).replace('隻', '只')
                                                                               .replace('迴憶', '回憶')
                                                                               .replace('瞭', '了')
                                                                               .replace('傢', '家')
                                                                               .replace('麵', '面')
                                                                               .replace('鞦天', '秋天')
                                                                               .replace('鞦色', '秋色')
                                                                               .replace('颱', '台'))
        #generated_lyrics.append(''.join(output_format))
        input_sentence = sentence_now
    return generated_lyrics, ch_position_num

# main page for lyrics demo
def lyrics(req):
    if req.method == 'POST':
        rhyme = RHYME_LIST[int(req.POST['rhyme'])].split(' ')[0]
        #first_sentence = req.POST['first_sentence'] if req.POST['first_sentence']!='' else None
        first_sentence = None
        keywords = req.POST['keywords']
        hid_sentence = req.POST['hidden_sentence'] if req.POST['hidden_sentence'] else None
        length = req.POST['length'] if req.POST['length'] != '' else None
        pattern = req.POST['pattern']
        if pattern == '3':
            selected_index = req.POST['selected_index']
        else:
            selected_index = None
        # print (selected_index)
        if length != None:
            length = re.sub('[^0-9;]','', length)
            length = length.strip(';').split(';')

        model_output, ch_position_num = gen_model_input(rhyme, first_sentence, keywords, hid_sentence,\
                                      length, pattern, selected_index)
        print (model_output)
        
        generated_lyrics = list(zip(model_output, ch_position_num))
        print (generated_lyrics)

        return render(req, 'index.html', {'rhyme_list': RHYME_LIST,
                                          # TODO: Frontend, only condition left
                                          'generated_lyrics': generated_lyrics,
                                          'hidden_sentence': hid_sentence,
                                          'rhyme': rhyme})

    elif req.method == 'GET':
        #generate_sentence('SOS 夜 空 真 美 EOS 1 1 你 || || u || 5')
        #child.expect(['\n>', pexpect.EOF, pexpect.TIMEOUT])
        return render(req, 'index.html', {'rhyme_list': RHYME_LIST})


