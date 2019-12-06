export CUDA_VISIBLE_DEVICES="2"
export Acrostic_HOME=$PWD
export Acrostic_TRAIN="$Acrostic_HOME/custom_t2t"
export Acrostic_DEMO="$Acrostic_HOME/demo_site"

python3 $Acrostic_DEMO/manage.py runserver 0.0.0.0:8895
