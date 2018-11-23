# pytorch-ssd for TME Dataset

A Pytorch implementation of Single Shot MultoBox Detector. The original code can be found [here](https://github.com/qijiezhao/pytorch-ssd). 


&nbsp;
&nbsp;

## Installation
For installation, you can follow this repository (https://github.com/amdegroot/ssd.pytorch)
The only difference is that this code is perfectly operated with pytorch 0.4.0.

## Modification
I added some Modules such as Extension Module and Spatial Weight Module for accurate vehicle detection.

<img align="left" src= "https://github.com/kimna4/SSD_TME/blob/master/doc/ssd_tme.png">

\
<br />
<br />
<br />
<br />



## TME Dataset
You can get the TME Dataset from here (http://cmp.felk.cvut.cz/data/motorway/).


## Training 
- First download the fc-reduced [VGG-16](https://arxiv.org/abs/1409.1556) PyTorch base network weights at:              https://s3.amazonaws.com/amdegroot-models/vgg16_reducedfc.pth
- By default, we assume you have downloaded the file in the `ssd.pytorch/weights` dir:

```Shell
mkdir weights
cd weights
wget https://s3.amazonaws.com/amdegroot-models/vgg16_reducedfc.pth
```

- To train SSD_TME using the train script simply specify the parameters listed in `train_tme_sw_deconv.py` as a flag or manually change them.

```Shell
python train_tme_sw_deconv.py
```



