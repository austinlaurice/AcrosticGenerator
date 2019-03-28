def process_rhyme_list():
    with open('freq.txt', 'r') as fr, open('tmp.txt', 'w') as fw:
        count = 0
        rhyme = ''
        #i 85947
        #[('你', 16620), ('里', 6285), ('起', 3153), ('子', 2993), ('己', 2782)]
        for line in fr:
            if count % 2 == 0:
                rhyme = line.split(' ')[0]
            else:
                line = line.strip().replace('(', '').replace('[', '').replace("'", '').split(',')
                characters = line[0::2]
                characters = '(' + ','.join(characters) + ')'
                fw.write('\t"' + rhyme + ' ' + characters + '",\n')
            count += 1

def main():
    process_rhyme_list()

if __name__ == '__main__':
    main()
