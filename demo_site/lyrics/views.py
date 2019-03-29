from django.shortcuts import render
from .misc import RHYME_LIST
import random
from collections import defaultdict
import re

def gen_model_input(rhyme, first_sentence, keywords, hid_sentence, length, pattern, selected_index):
    # rhyme is already done
    line_count = 6
    zero_sentence = None
    # Need to decide how many lines first
    if (pattern == '0' or pattern == '1') and hid_sentence != None:
        line_count = len(hid_sentence)
    elif length != None:
        line_count = len(length)
    if not first_sentence:
        pass
        # TODO
        # zero_sentence = gen_first_sentence(keywords) # if no keyword then random generate a sentence

    # Use pattern to decide the condition of each sentence
    # length of each sentence is decided in this section
    ch_position = []
    if pattern == '0': #first character of each sentence
        for ch in hid_sentence:
            ch_position.append([(1, ch)])
    elif pattern == '1': #last character of each sentence
        if length:
            for position, ch in zip(length, hid_sentence):
                ch_position.append([(int(position), ch)])
        else:
            length = [random.randint(6, 16) for _ in range(len(hid_sentence))]
            for position, ch in zip(length, hid_sentence):
                ch_position.append([(int(position), ch)])
    elif pattern == '2':
        position = 1
        if length:
            for ch in hid_sentence:
                ch_position.append([(position, ch)])
                position += 1
        else:
            length = [x+1+random.randint(2, 10) for x in range(len(hid_sentence))]
            for ch in hid_sentence:
                ch_position.append([(position, ch)])
                position += 1
    elif pattern == '3':
        # selected_index 0_0 1_0 1_1 need to plus one for col index
        selected_index = selected_index.strip().split(' ')
        selected_position = defaultdict(list)
        for index in selected_index:
            row, col = index.split('_')
            selected_position[int(row)].append(int(col)+1)
        if length:
            ch_count = 0
            for i in range(len(length)):
                ch_row = []
                position_now = sorted(selected_position[i]) if i in selected_position else None
                if position_now:
                    for position in position_now:
                        ch_row.append((position, hid_sentence[ch_count]))
                        ch_count += 1
                ch_position.append(ch_row)
        else:
            length = [15] * 6
            # 6 * 15
            ch_count = 0
            for i in range(len(length)):
                ch_row = []
                position_now = sorted(selected_position[i]) if i in selected_position else None
                if position_now:
                    for position in position_now:
                        ch_row.append((position, hid_sentence[ch_count]))
                        ch_count += 1
                ch_position.append(ch_row)

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
                        condition = str(c) + ' ' + p + ' '
                        condition_count += 1
                    condition = str(condition_count) + ' ' + condition
                else:
                    condition = '0 '
                input_sentence = 'SOS ' + zero_sentence + ' EOS ' + condition + \
                                 '|| ' + rhyme + ' || ' + str(length_row)
                # TODO
                # model need to be called by here
                # sentence_now = generate_sentence(input_sentence)
            else:
                sentence_now = first_sentence
        else:
            condition_count = 0
            if len(ch_position[row_num]) != 0:
                condition = ''
                for c, p in ch_position[row_num]:
                    condition = str(c) + ' ' + p + ' '
                    condition_count += 1
                condition = str(condition_count) + ' ' + condition
            else:
                condition = '0 '
            input_sentence = 'SOS ' + input_sentence + ' EOS ' + condition + \
                             '|| ' + rhyme + ' || ' + str(length_row)
            # TODO
            # model need to be called by here
            # sentence_now = generate_sentence(input_sentence)
        print (input_sentence)
        generated_lyrics.append(sentence_now)
        input_sentence = sentence_now
    return generated_lyrics

# main page for lyrics demo
def lyrics(req):
    if req.method == 'POST':
        rhyme = RHYME_LIST[int(req.POST['rhyme'])].split(' ')[0]
        first_sentence = req.POST['first_sentence'] if req.POST['first_sentence']!='' else None
        keywords = req.POST['keywords'] if req.POST['keywords'] != '' else None
        hid_sentence = req.POST['hidden_sentence'] if req.POST['hidden_sentence'] else None
        length = req.POST['length'] if req.POST['length'] != '' else None
        pattern = req.POST['pattern']
        if pattern == '3':
            selected_index = req.POST['selected_index']
        else:
            selected_index = None
        print (selected_index)
        if length != None:
            length = re.sub('[^0-9;]','', length)
            length = length.split(';')

        model_input = gen_model_input(rhyme, first_sentence, keywords, hid_sentence,\
                                      length, pattern, selected_index)



        return render(req, 'index.html', {'rhyme_list': RHYME_LIST,
                                          # TODO: Frontend
                                          'generated_lyrics': first_sentence})

    elif req.method == 'GET':
        return render(req, 'index.html', {'rhyme_list': RHYME_LIST})


