from django.shortcuts import render
from .models import Locker
from .misc_english import RHYME_LIST
from .models import Locker
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

locks = Locker.objects.all()
if len(locks) == 0:
    lock = Locker.objects.create()
    lock.save()
if locks[0].is_using == True:
    locks[0].is_using = False
    locks[0].save()



# generate a lock if not exist
all_locks = Locker.objects.all()
if len(all_locks) == 0:
    lock = Locker.objects.create()
    lock.save()
if all_locks[0].is_using == True:
    all_locks[0].is_using = False
    all_locks[0].objects.save()


def generate_sentence(input_sentence):
    print (input_sentence)
    child.sendline(input_sentence)
    child.expect(['\n>', pexpect.EOF, pexpect.TIMEOUT])
    #output = re.search(r'INFO.*SOS.*\n', child.before) # parse output
    output = re.search(r'INFO.*.*\n', child.before) # parse output
    if output:
        sentence_generated = output.group().split(':')[-1]
        sentence_generated = sentence_generated.strip().replace('SOS ', '').replace('<EOS>', '')
        return sentence_generated


# word match method
'''
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
    if len(input_lyric) > 4 and len(output_lyric) > 4:
        if input_lyric[:4] == output_lyric[:4]:
            return False
        if input_lyric[-4:] == output_lyric[-4:]:
            return False
    if Counter(output_lyric_bigrams).most_common(1)[0][1] > 2:
        return False
    if Counter(input_lyric_bigrams + output_lyric_bigrams).most_common(1)[0][1] > 3:
        return False
    if len(set(input_lyric_bigrams) & set(output_lyric_bigrams)) / len(set(output_lyric_bigrams)) > 0.3:
        return False
    
    return True
'''
def gen_model_input(rhyme, first_sentence, keywords, hid_sentence, length, pattern, selected_index, length_word):

    # rhyme is already done
    line_count = 6
    zero_sentence = None
    # Need to decide how many lines first
    #hid_sentence = HanziConv.toSimplified(hid_sentence)
    hid_sentence = hid_sentence.split(' ')
    if (pattern == '0' or pattern == '1') and hid_sentence != None:
        line_count = len(hid_sentence)
    elif length != None:
        line_count = len(length)
    #if not first_sentence:
        #import ipdb; ipdb.set_trace()
    #    if keywords:
            #keywords = HanziConv.toSimplified(keywords)
    #        keywords = keywords.strip().split(' ')

    zero_sentence = first_sentence
    #zero_sentence = ' '.join(zero_sentence.replace(' ', ''))
    #else:
    #    first_sentence = ' '.join(HanziConv.toSimplified(first_sentence).strip())
    # Use pattern to decide the condition of each sentence
    # length of each sentence is decided in this section
    word_position = []
    word_position_num = []
    if pattern == '0': #first character of each sentence
        if not length:
            length = [random.randint(6, 16) for _ in range(len(hid_sentence))]
        for word in hid_sentence:
            word_position.append([(1, word)])
            word_position_num.append([1])
    elif pattern == '1': #last character of each sentence
        if length:
            for position, word in zip(length, hid_sentence):
                word_position.append([(int(position), word)])
                word_position_num.append([int(position)])
        else:
            length = [random.randint(6, 16) for _ in range(len(hid_sentence))]
            for position, word in zip(length, hid_sentence):
                word_position.append([(int(position), word)])
                word_position_num.append([int(position)])
    elif pattern == '2':
        position = 1
        if length:
            for word in hid_sentence:
                word_position.append([(position, word)])
                word_position_num.append([position])
                position += 1
        else:
            length = [x+1+random.randint(2, 10) for x in range(len(hid_sentence))]
            for word in hid_sentence:
                word_position.append([(position, word)])
                word_position_num.append([position])
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
                word_position.append(ch_row)
                word_position_num.append(ch_row_num)
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
                word_position.append(ch_row)
                word_position_num.append(ch_row_num)

    # word_position = [[row0], [row1], ....]; rhyme = 'u'; length = [11, 12, 13]; hid_sentence = '你好'
    # length_word = [[1, 2, 3], [4, 4, 4]]
    # generate first sentence if there's zero sentence
    generated_lyrics = []
    input_sentence = ''
    sentence_now = ''
    #import ipdb; ipdb.set_trace()
    for row_num, length_row in enumerate(length):
            length_word_row = ''
            if length_word:
                length_word_row = ' '.join(length_word[row_num])
            if row_num == 0:
                if zero_sentence:
                    condition_count = 0
                    if len(word_position[row_num]) != 0:
                        condition = ''
                        for c, p in word_position[row_num]:
                            condition = condition + str(c) + ' ' + p + ' '
                            condition_count += 1
                        condition = str(condition_count) + ' ' + condition
                    else:
                        condition = '0 '

                    input_sentence = zero_sentence+ '<EOS>' + ' ' + condition + '|| ' + \
                                     rhyme + ' || ' + length_word_row + ' || '+ str(length_row)
                    
                    # and it means something special to me 2 7 smiles 6 she || IY1 || 4 2 3 3 4 3 6 4 3 4 2 || 11, look at the way that she smiles when she sees me
                    
                    sentence_now = generate_sentence(input_sentence)
                    #sentence_now = generate_sentence(input_sentence)
                else:
                    sentence_now = first_sentence
            else:
                #illegal = True
                #padded_sentence_index = row_num
                #print("="*80)
                #original_input_sentence = input_sentence
                #count = 0
                #while illegal and padded_sentence_index >= 0:
                #    condition_count = 0
                if len(word_position) < row_num+1:
                    condition = '0 '
                elif len(word_position[row_num]) != 0:
                    condition = ''
                    for c, p in word_position[row_num]:
                        condition = condition + str(c) + ' ' + p + ' '
                        condition_count += 1
                    condition = str(condition_count) + ' ' + condition
                else:
                    condition = '0 '
                new_input_sentence = input_sentence + ' ' + condition + '|| ' + \
                                     rhyme + ' || ' + length_word_row + ' || '+ str(length_row)
                    # TODO
                    # model need to be called by here
                    #if not zero_sentence and row_num == 1:
                    #    sentence_now = generate_sentence(input_sentence)
                sentence_now = generate_sentence(new_input_sentence)
                print('sentence_now', sentence_now)
                print('row_num', row_num)
                    
                    #if not isLegalSentence(original_input_sentence, sentence_now):
                    #    print("ILLEGAL!!!!!!!!!!!")
                    #    pos_string = POS_LEN_TABLE[int(length_row)][count]
                    #    count += 1
                        #padded_sentence_index = min(padded_sentence_index, len(generated_lyrics)-1)
                        #padded_sentence_index -= 1
                        #if row_num == 1 or padded_sentence_index == -1:
                        #    input_sentence = zero_sentence + ' ' + input_sentence
                        #else:
                        #    input_sentence = ' '.join(list(HanziConv.toSimplified(generated_lyrics[padded_sentence_index]))) + ' ' + input_sentence
                    #else:
                    #    illegal = False
                print(input_sentence)



            print (sentence_now)
            output_format = sentence_now.split(' ')
            #for position in ch_position[row_num]:
            #    try:
            #        output_format[position[0]-1] = position[1]
            #    except IndexError:
            #        print ('Generated sentence is defferent from the condition.')
            #        continue
            
            generated_lyrics.append(output_format)
            #generated_lyrics.append(''.join(output_format))
            input_sentence = sentence_now
    return generated_lyrics, word_position_num

# main page for lyrics demo
def lyrics(req):
    if req.method == 'POST':
        # Need to require lock first
        lock = Locker.objects.all()[0]
        while(lock.is_using == True):
            lock = Locker.objects.all()[0]
        lock.is_using = True
        lock.save()
        rhyme = RHYME_LIST[int(req.POST['rhyme'])].split(' ')[0]
        #first_sentence = req.POST['first_sentence'] if req.POST['first_sentence']!='' else None
        #first_sentence = None
        keywords = req.POST['keywords'] if req.POST['keywords'] else "where should i go"
        print('keywords', keywords)
        # Use keywords as zeroth sentence
        first_sentence = keywords.replace(',', '').replace('.', '')
        #if first_sentence == '':
        #    first_sentence = 'where should i go'
        hid_sentence = req.POST['hidden_sentence'] if req.POST['hidden_sentence'] else None
        length = req.POST['length'] if req.POST['length'] != '' else None
        length_word = req.POST['length_word'] if req.POST['length_word'] != '' else None
        pattern = req.POST['pattern']
        if pattern == '3':
            selected_index = req.POST['selected_index']
        else:
            selected_index = None
        # print (selected_index)
        if length != None:
            length = re.sub('[^0-9;]','', length)
            length = length.strip(';').split(';')
            print (length)

        if length_word != None:
            length_word = re.sub('[^0-9;|]','', length_word)
            length_word = length_word.strip('||').split('||')
            length_word = [x.split(';') for x in length_word]

        model_output, ch_position_num, keywords_record, rhyme_record = [], [], [], []

        rhy = rhyme
        key = keywords
        if rhyme == "":
            for rhyme in RHYME_LIST[1:6]:
                rhy = rhyme.split()[0]
                if keywords == "":
                    for _ in range(3):
                        tmp_model_output, tmp_ch_position_num = gen_model_input(rhy,\
                                                                                first_sentence, key,\
                                                                                hid_sentence, length,\
                                                                                pattern, selected_index,\
                                                                                length_word)
                        model_output.append(tmp_model_output)
                        ch_position_num.append(tmp_ch_position_num)
                        keywords_record.append([key])
                        rhyme_record.append([rhy])
                else:
                    tmp_model_output, tmp_ch_position_num = gen_model_input(rhy,\
                                                                            first_sentence, key,\
                                                                            hid_sentence, length,\
                                                                            pattern, selected_index,\
                                                                            length_word)
                    model_output.append(tmp_model_output)
                    ch_position_num.append(tmp_ch_position_num)
                    keywords_record.append([key])
                    rhyme_record.append([rhy])
        else:
            if keywords == "":
                for _ in range(3):
                    tmp_model_output, tmp_ch_position_num = gen_model_input(rhy, first_sentence, key,\
                                                                        hid_sentence, length, pattern,\
                                                                        selected_index, length_word)
                    model_output.append(tmp_model_output)
                    ch_position_num.append(tmp_ch_position_num)
                    keywords_record.append([key])
                    rhyme_record.append([rhy])
            else:
                tmp_model_output, tmp_ch_position_num = gen_model_input(rhy, first_sentence, key,\
                                                                    hid_sentence, length, pattern, \
                                                                    selected_index, length_word)
                model_output.append(tmp_model_output)
                ch_position_num.append(tmp_ch_position_num)
                keywords_record.append([key])
                rhyme_record.append([rhy])
        print (model_output)
        print('keywords_record', keywords_record)
        print('rhyme_record', rhyme_record)
        
        generated_lyrics = []
            
        for mod, ch, key, rhy in list(zip(model_output, ch_position_num, keywords_record, rhyme_record)):
            #import ipdb; ipdb.set_trace()
            while(len(mod) > len(ch)):
                ch.append([])
            generated_lyrics.append(list(zip(mod, ch)) + key + rhy)

        print (generated_lyrics)
        lock.is_using = False
        lock.save()

        lock.is_using = False
        lock.save()

        return render(req, 'index.html', {'rhyme_list': RHYME_LIST,
                                          'generated_lyrics': generated_lyrics,
                                          'hidden_sentence': hid_sentence,
                                          'rhyme': rhyme})

    elif req.method == 'GET':
        #generate_sentence('SOS 夜 空 真 美 EOS 1 1 你 || || u || 5')
        #child.expect(['\n>', pexpect.EOF, pexpect.TIMEOUT])
        return render(req, 'index.html', {'rhyme_list': RHYME_LIST})


