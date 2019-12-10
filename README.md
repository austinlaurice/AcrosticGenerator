
Neural-based Acrostic Generator
===

This is the source code of the demo site in ["Controlling Sequence-to-Sequence Models - A Demonstration on Neural-based Acrostic Generator"](https://www.aclweb.org/anthology/D19-3008/). The paper demonstrates how to generate acrostic based on a sequence-to-sequence model.


## How to set up the demo site

1. Check everything is placed in the right place written in [this command](https://github.com/austinlaurice/Lyrics_demo/blob/7feb8549e79d84bb9b4bc7299deb511a0687ed71/demo_site/lyrics/views.py#L21)

2. Run run_demo.sh which starts the demo site on port 8891


## How to use your own data to train

1. Place the data that have already been preprocessed in the data_dir in train.sh

2. Run train.sh

## Chinese Examples
<img src="/images/heart_demo.png"  width="300"/>
<img src="/images/mountain.png" width="300"/>
<img src="/images/dream.png" width="300"/>

## English Examples
![be_the_change_demo](/images/be_the_change.png)
![armstrong_demo](/images/armstrong.png)

## Citation
```
@inproceedings{shen-etal-2019-controlling,
    title = "Controlling Sequence-to-Sequence Models - A Demonstration on Neural-based Acrostic Generator",
    author = "Shen, Liang-Hsin  and
      Tai, Pei-Lun  and
      Wu, Chao-Chung  and
      Lin, Shou-De",
    booktitle = "Proceedings of the 2019 Conference on Empirical Methods in Natural Language Processing and the 9th International Joint Conference on Natural Language Processing (EMNLP-IJCNLP): System Demonstrations",
    month = nov,
    year = "2019",
    address = "Hong Kong, China",
    publisher = "Association for Computational Linguistics",
    url = "https://www.aclweb.org/anthology/D19-3008",
    doi = "10.18653/v1/D19-3008",
    pages = "43--48",
    abstract = "An acrostic is a form of writing that the first token of each line (or other recurring features in the text) forms a meaningful sequence. In this paper we present a generalized acrostic generation system that can hide certain message in a flexible pattern specified by the users. Different from previous works that focus on rule-based solutions, here we adopt a neural- based sequence-to-sequence model to achieve this goal. Besides acrostic, users are also allowed to specify the rhyme and length of the output sequences. Based on our knowledge, this is the first neural-based natural language generation system that demonstrates the capability of performing micro-level control over output sentences.",
}
```
## License
[Apache License](https://opensource.org/licenses/Apache-2.0)
