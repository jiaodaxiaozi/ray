# The examples Docker image adds dependencies needed to run the examples

FROM ray-project/deploy

# This updates numpy to 1.14 and mutes errors from other libraries
RUN conda install -y numpy
# Needed to run Tune example with a 'plot' call - which does not actually render a plot, but throws an error.
RUN apt-get install -y zlib1g-dev libgl1-mesa-dev
# The following is needed to support TensorFlow 1.14
RUN conda remove -y --force wrapt
RUN pip install -U pip
RUN pip install gym[atari] opencv-python-headless tensorflow lz4 keras pytest-timeout smart_open tensorflow_probability
RUN pip install -U h5py  # Mutes FutureWarnings
RUN pip install --upgrade bayesian-optimization
RUN pip install --upgrade hyperopt==0.1.2
RUN pip install ConfigSpace==0.4.10
RUN pip install --upgrade sigopt nevergrad scikit-optimize hpbandster lightgbm xgboost torch torchvision tensorboardX
RUN pip install -U tabulate mlflow
RUN pip install -U pytest-remotedata>=0.3.1
