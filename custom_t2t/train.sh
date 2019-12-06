CUDA_VISIBLE_DEVICES=0
t2t-trainer \
    --generate_data \
    --t2t_usr_dir=script \
    --problem=lyrics \
    --data_dir='./english_data' \
    --model=transformer \
    --hparams_set=transformer_base_single_gpu \
    --output_dir='./english_train' \
    --worker_gpu_memory_fraction=0.4 \
    --train_steps=1000000
