from tensor2tensor.data_generators import problem
from tensor2tensor.data_generators import text_problems
from tensor2tensor.layers import common_hparams
from tensor2tensor.utils import registry

import os

@registry.register_hparams
def lyrics_hparam():
    hp = common_hparams.basic_params1()
    hp.num_hidden_layers = 4
    return hp

@registry.register_problem
class Lyrics(text_problems.Text2TextProblem):

    @property
    def approx_vocab_size(self):
        return 50000

    @property
    def is_generate_per_split(self):
        return False

    @property
    def dataset_splits(self):
        # 10% evaluation
        data = [{"split": problem.DatasetSplit.TRAIN,
                 "shards": 9,
                },
                {"split": problem.DatasetSplit.EVAL,
                 "shards": 1,
                }]
        return data

    def generate_samples(self, data_dir, tmp_dir, dataset_split):
        del data_dir
        del tmp_dir
        del dataset_split

        # read my own data
        lyric = []
        target_lyric = []
        with open(f'{os.environ["Acrostic_TRAIN"]}/sample_data.txt', 'r') as fp:
            for line in fp:
                line = line.split(',')
                lyric.append(line[0])
                target_lyric.append(line[1])

        for x, y in zip(lyric, target_lyric):
            yield{
                "inputs": x,
                "targets": y
            }



