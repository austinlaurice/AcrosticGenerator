from django.shortcuts import render
from .misc import RHYME_LIST
# Create your views here.

# TODO
def gen_model_input(rhyme, first_sentence, keywords, hid_sentence, length, pattern, selected_index):
    pass
    #if first_sentence


# main page for lyrics demo
def lyrics(req):
    if req.method == 'POST':
        rhyme = RHYME_LIST[int(req.POST['rhyme'])].split(' ')[0]
        first_sentence = req.POST['first_sentence'] if req.POST['first_sentence']!='' else None
        keywords = req.POST['keywords'] if req.POST['keywords'] != '' else None
        hid_sentence = req.POST['hidden_sentence'] if req.POST['hidden_sentence'] else None
        length = req.POST['length'] if req.POST['length'] != '' else None
        pattern = req.POST['pattern']
        if pattern == 3:
            selected_index = req.POST['selected_index']
        else:
            selected_index = None
        # TODO
        # Need to decide how many lines first
        model_input = gen_model_input(rhyme, first_sentence, keywords, hid_sentence,
                                      length, pattern, selected_index)



        return render(req, 'index.html', {'rhyme_list': RHYME_LIST,
                                          # TODO
                                          'generated_lyrics': first_sentence})

    elif req.method == 'GET':
        return render(req, 'index.html', {'rhyme_list': RHYME_LIST})


