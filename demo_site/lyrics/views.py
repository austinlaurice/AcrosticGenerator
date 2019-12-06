from django.shortcuts import render
from .misc import RHYME_LIST
from .models import Locker
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
import logging
from opencc import OpenCC
from hanziconv import HanziConv


cmd = ['t2t-decoder',
       f'--t2t_usr_dir={os.environ["Acrostic_TRAIN"]}/script',
       '--problem=lyrics',
       f'--data_dir={os.environ["Acrostic_TRAIN"]}/chinese_data',
       '--model=transformer',
       '--hparams_set=transformer_base_single_gpu',
       f'--output_dir={os.environ["Acrostic_TRAIN"]}/chinese_train',
       '--decode_interactive',
       '--worker_gpu_memory_fraction=0.1']


# run t2t-decoder as child process
child = pexpect.spawn(' '.join(cmd), encoding='utf-8')

# expect the '>' token of t2t-decoder output
# not a good method, but I haven't thought of a better way to read multi-line output from child.
child.expect('\n>', timeout=200)

# This is used for some randomness while generating data (NOT necessary)
# It's POS tagging, which was original used while training.
with open(f'{os.environ["Acrostic_TRAIN"]}/pos_table.pkl', 'rb') as f:
    POS_LEN_TABLE = pickle.load(f)


# generate a lock if not exist
all_locks = Locker.objects.all()
if len(all_locks) == 0:
    lock = Locker.objects.create()
    lock.save()
if all_locks[0].is_using == True:
    all_locks[0].is_using = False
    all_locks[0].save()

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('[%(asctime)s]:\t%(message)s')
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.DEBUG)
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)


def create_input(content='', position_assign='', rhyme='', POS='', length='', sep='||', SOS='SOS', EOS='EOS'):
    L = [SOS, content, EOS, position_assign, sep, POS, sep, rhyme, sep, length]
    return ' '.join([i for i in L if i is not ''])


def generate_sentence(input_sentence):
    logger.info(f'[generate_sentence] input_sentence: {input_sentence}')
    child.sendline(input_sentence)
    child.expect(['\n>', pexpect.EOF, pexpect.TIMEOUT])
    output = re.search(r'INFO.*SOS.*\n', child.before) # parse output
    if output:
        sentence_generated = output.group().split(':')[-1]
        sentence_generated = sentence_generated.strip().replace('SOS ', '').replace(' EOS', '')
        return sentence_generated


def isLegalSentence(original_input_sentence, sentence_now):
    if sentence_now == None:
        return False
    input_lyric = ['SOS'] + original_input_sentence.split() + ['EOS']
    input_lyric_bigrams = [tuple(input_lyric[i:i+2]) for i in range(len(input_lyric)-2)]
    output_lyric = ['SOS'] + sentence_now.split() + ['EOS']
    output_lyric_bigrams = [tuple(output_lyric[i:i+2]) for i in range(len(output_lyric)-2)]
    # same bigram should not appear over 2 times in a sentence
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


def gen_model_input(rhyme, keywords, hidden_sentence, length, pattern, selected_index):
    line_count = 6
    zero_sentence = None
    # Need to decide how many lines first
    hidden_sentence = HanziConv.toSimplified(hidden_sentence)
    if (pattern == '0' or pattern == '1') and hidden_sentence != None:
        line_count = len(hidden_sentence)
    elif length != None:
        line_count = len(length)
    if keywords:
        keywords = HanziConv.toSimplified(keywords)
        keywords = keywords.strip().split(' ')
        
    zero_sentence = ' '.join(hidden_sentence)  # Use the hidden sentence as zero_sentence
    
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
        logger.info(f'row_num: {row_num}')
        if row_num == 0:
            condition_count = 0
            if len(ch_position[row_num]) != 0:
                condition = ''
                for c, p in ch_position[row_num]:
                    condition = condition + str(c) + ' ' + p + ' '
                    condition_count += 1
                condition = str(condition_count) + ' ' + condition.strip()
            else:
                condition = '0'
            input_sentence = create_input(content=zero_sentence,
                                          position_assign=condition,
                                          rhyme=rhyme,
                                          length=str(length_row))
            #SOS 心 疼 你 还 没 挣 脱 思 念 的 囚 禁 EOS 2 11 后 1 他 || r p r m m v v v v f f d v v || u || 14,SOS 他 在 你 一 段 难 忘 远 行 最 后 却 离 去 EOS
            sentence_now = generate_sentence(input_sentence)
        else:
            illegal = True
            padded_sentence_index = row_num
            logger.info("="*80)
            original_input_sentence = input_sentence
            retry_count = 0
            pos_string = ''
            while illegal and padded_sentence_index >= 0:
                condition_count = 0
                if len(ch_position[row_num]) != 0:
                    condition = ''
                    for c, p in ch_position[row_num]:
                        condition = condition + str(c) + ' ' + p + ' '
                        condition_count += 1
                    condition = str(condition_count) + ' ' + condition
                else:
                    condition = ''
                new_input_sentence = create_input(content=input_sentence,
                                                  position_assign=condition,
                                                  rhyme=rhyme,
                                                  length=str(length_row))
                sentence_now = generate_sentence(new_input_sentence)
                logger.info(f'sentence_now: {sentence_now}')
                logger.info(f'row_num: {row_num}')
                
                if not isLegalSentence(original_input_sentence, sentence_now):
                    logger.info("ILLEGAL!!!!!!!!!!!")
                    if (retry_count >= 5):
                        break
                    if retry_count < 2:
                        padded_sentence_index = min(padded_sentence_index, len(generated_lyrics)-1)
                        padded_sentence_index -= 1
                        if row_num == 1 or padded_sentence_index == -1:
                            input_sentence = zero_sentence + ' ' + input_sentence
                        else:
                            input_sentence = ' '.join(list(HanziConv.toSimplified(generated_lyrics[padded_sentence_index]))) + ' ' + input_sentence
                    else:
                        input_sentence = original_input_sentence
                        try:
                            pos_string = random.choice(POS_LEN_TABLE[int(length_row)])
                            retry_count += 1
                        except:
                            break
                else:
                    illegal = False

                logger.info(f'input_sentence: {input_sentence}')

        logger.info(f'sentence_now: {sentence_now}')

        output_format = sentence_now.split(' ')
        
        generated_lyrics.append(HanziConv.toTraditional(''.join(output_format)).replace('隻', '只')
                                                                               .replace('迴憶', '回憶')
                                                                               .replace('瞭', '了')
                                                                               .replace('傢', '家')
                                                                               .replace('麵', '面')
                                                                               .replace('鞦天', '秋天')
                                                                               .replace('鞦色', '秋色')
                                                                               .replace('颱', '台')
                                                                               .replace('纔', '才')
                                                                               .replace('齣', '出')
                                                                               .replace('纍了', '累了')
                                                                               .replace('紮', '扎'))
        input_sentence = sentence_now
    return generated_lyrics, ch_position_num


# main page for lyrics demo
def lyrics(req):
    if req.method == 'POST':
        lock = Locker.objects.all()[0]
        while(lock.is_using == True):
            lock = Locker.objects.all()[0]
        lock.is_using = True
        lock.save()

        form = PostForm(req.POST or None)
        if form.is_valid():
            rhyme = form.cleaned_data['rhyme']
            keywords = form.cleaned_data['keywords']
            hidden_sentence = form.cleaned_data['hidden_sentence'].strip().replace(' ', '')
            fill_len = max(len(hidden_sentence), 10)
            # Set length if length is not given
            if form.cleaned_data['length'].strip() == '':
                form.cleaned_data['length'] = ';'.join([str(fill_len)]*len(hidden_sentence))
            length = form.cleaned_data['length']
            pattern = form.cleaned_data['pattern']

        if int(rhyme) == 0:   # randomly choose a rhyme if not given
            rhyme = random.choice(RHYME_LIST[1:])[1].split(' ')[0]
        else:
            rhyme = RHYME_LIST[int(rhyme)][1].split(' ')[0]
        
        if keywords.strip() == '':
            keywords = hidden_sentence

        logger.info(f"selected: {req.POST['selected_index']}")
        selected_index = req.POST['selected_index']
        length = re.sub('[^0-9;]','', length)
        length = length.strip(';').split(';')

        generated_lyrics = []
        try:
            model_output, ch_position_num = gen_model_input(rhyme, keywords,\
                                                            hidden_sentence, length,\
                                                            pattern, selected_index)

            lock.is_using = False
            lock.save()
            generated_lyrics = list(zip(model_output, ch_position_num))
            logger.info(f'generated_lyrics: {generated_lyrics}')

        except:
            pass

        return render(req, 'index.html', {'rhyme_list'      : RHYME_LIST,
                                          'generated_lyrics': generated_lyrics,
                                          'hidden_sentence' : hidden_sentence,
                                          'rhyme'           : rhyme,
                                          'form'            : form,
                                          'selected_index'  : selected_index})

    elif req.method == 'GET':
        form = PostForm()
        return render(req, 'index.html', {'rhyme_list': RHYME_LIST, 'form': form})
