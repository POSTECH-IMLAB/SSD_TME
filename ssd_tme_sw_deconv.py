import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.autograd import Variable
from layers import *
from data import v as cfg
import os
from IPython import embed


class SSD(nn.Module):
    """Single Shot Multibox Architecture
    The network is composed of a base VGG network followed by the
    added multibox conv layers.  Each multibox layer branches into
        1) conv2d for class conf scores
        2) conv2d for localization predictions
        3) associated priorbox layer to produce default bounding
           boxes specific to the layer's feature map size.
    See: https://arxiv.org/pdf/1512.02325.pdf for more details.

    Args:
        phase: (string) Can be "test" or "train"
        base: VGG16 layers for input, size of either 512
        extras: extra layers that feed to multibox loc and conf layers
        head: "multibox head" consists of loc and conf conv layers
    """

    def __init__(self, phase, size, base, extras, head, num_classes):
        super(SSD, self).__init__()
        self.phase = phase
        self.num_classes = num_classes
        # TODO: implement __call__ in PriorBox
        self.priorbox = PriorBoxTme(cfg[str(size)])
        # self.priors = Variable(self.priorbox.forward(), volatile=True)
        with torch.no_grad():
            self.priors = Variable(self.priorbox.forward())
        self.size = size

        # SSD network
        self.vgg = nn.ModuleList(base)
        # Layer learns to scale the l2 normalized features from conv4_3
        self.L2Norm = L2Norm(512, 20)
        self.extras = nn.ModuleList(extras[0])
        self.sw_layers = nn.ModuleList(extras[1])
        self.ex_layers = nn.ModuleList(extras[2])

        self.loc = nn.ModuleList(head[0])
        self.conf = nn.ModuleList(head[1])

        if self.phase == 'test':
            self.softmax = nn.Softmax(dim=-1)
            self.detect = Detect(num_classes, self.size, 0, 200, 0.01, 0.45)

    def forward(self, x):
        """Applies network layers and ops on input image(s) x.

        Args:
            x: input image or batch of images. Shape: [batch,3,300,300]. or [batch,3,512,512]

        Return:
            Depending on phase:
            test:
                Variable(tensor) of output class label predictions,
                confidence score, and corresponding location predictions for
                each object detected. Shape: [batch,topk,7]

            train:
                list of concat outputs from:
                    1: confidence layers, Shape: [batch,num_priors,num_classes]
                    2: localization layers, Shape: [batch,num_priors,4]
                    3: priorbox layers, Shape: [num_priors,4]
        """
        sources = list()
        loc = list()
        conf = list()
        # x: (batch, channel, height, width)
        # apply vgg up to conv4_3 relu
        for k in range(23):
            x = self.vgg[k](x)

        s = self.L2Norm(x)
        sources.append(s)

        # SW block 1
        x_sw = F.relu(self.sw_layers[0](x), inplace=True)
        x_sw = F.tanh(self.sw_layers[1](x_sw))
        x = x + x_sw

        # apply vgg up to fc7
        for k in range(23, len(self.vgg)):
            x = self.vgg[k](x)
        sources.append(x)

        # SW block 2
        x_sw = F.relu(self.sw_layers[2](x), inplace=True)
        x_sw = F.tanh(self.sw_layers[3](x_sw))
        x = x + x_sw

        sw_flag = True
        # apply extra layers and cache source layer outputs
        for k, v in enumerate(self.extras):
            x = F.relu(v(x), inplace=True)
            if k % 2 == 1:
                sources.append(x)
                if sw_flag == True:
                    # SW block 3
                    x_sw = F.relu(self.sw_layers[4](x), inplace=True)
                    x_sw = F.tanh(self.sw_layers[5](x_sw))
                    x = x + x_sw
                    sw_flag = False

        # Extension Module을 삽입
        sources_ex = []
        for k in range(4):
            target_x = sources[k]
            next_x = sources[k + 1]
            x_ne = F.relu(self.ex_layers[k * 4](next_x), inplace=True)
            x_ne = F.relu(self.ex_layers[k * 4 + 1](x_ne), inplace=True)
            x_tar = F.relu(self.ex_layers[k * 4 + 2](target_x), inplace=True)
            x_tar = F.relu(self.ex_layers[k * 4 + 3](x_tar), inplace=True)
            sources_ex.append(x_ne + x_tar)
        sources_ex.append(sources[4])
        sources_ex.append(sources[5])
        sources_ex.append(sources[6])

        # apply multibox head to source layers
        for (x, l, c) in zip(sources_ex, self.loc, self.conf):
            loc.append(l(x).permute(0, 2, 3, 1).contiguous())
            conf.append(c(x).permute(0, 2, 3, 1).contiguous())

        loc = torch.cat([o.view(o.size(0), -1) for o in loc], 1)
        conf = torch.cat([o.view(o.size(0), -1) for o in conf], 1)
        if self.phase == "test":
            output = self.detect(
                loc.view(loc.size(0), -1, 4),                   # loc preds
                # self.softmax(conf.view(-1, self.num_classes)),  # conf preds
                self.softmax(conf.view(conf.size(0), -1,
                                       self.num_classes)),  # conf preds
                self.priors.type(type(x.data))                  # default boxes
            )
        else:
            output = (
                loc.view(loc.size(0), -1, 4),
                conf.view(conf.size(0), -1, self.num_classes),
                self.priors
            )
        return output

    def load_weights(self, base_file):
        other, ext = os.path.splitext(base_file)
        if ext == '.pkl' or '.pth':
            print('Loading weights into state dict...')
            self.load_state_dict(torch.load(base_file, map_location=lambda storage, loc: storage))
            print('Finished!')
        else:
            print('Sorry only .pth and .pkl files supported.')


# This function is derived from torchvision VGG make_layers()
# https://github.com/pytorch/vision/blob/master/torchvision/models/vgg.py
def vgg(cfg, i, batch_norm=False):
    layers = []
    in_channels = i
    for v in cfg:
        if v == 'M':
            layers += [nn.MaxPool2d(kernel_size=2, stride=2)]
        elif v == 'C':
            layers += [nn.MaxPool2d(kernel_size=2, stride=2, ceil_mode=True)]
        else:
            conv2d = nn.Conv2d(in_channels, v, kernel_size=3, padding=1)
            if batch_norm:
                layers += [conv2d, nn.BatchNorm2d(v), nn.ReLU(inplace=True)]
            else:
                layers += [conv2d, nn.ReLU(inplace=True)]
            in_channels = v
    pool5 = nn.MaxPool2d(kernel_size=3, stride=1, padding=1)
    conv6 = nn.Conv2d(512, 1024, kernel_size=3, padding=6, dilation=6)
    conv7 = nn.Conv2d(1024, 1024, kernel_size=1)
    layers += [pool5, conv6,
               nn.ReLU(inplace=True), conv7, nn.ReLU(inplace=True)]
    return layers

def SW_modules(in_channels):
    SW_layers = []
    SW_layers += [nn.Conv2d(in_channels, in_channels * 2, kernel_size=1, stride=1)]
    # SW_layers += [nn.ReLU(inplace=True)]
    SW_layers += [nn.Conv2d(in_channels * 2, 1, kernel_size=1, stride=1)]
    # SW_layers += [nn.Tanh()]
    return SW_layers

def Extension_modules(in_channels, out_channels):
    EX_layers = []
    EX_layers += [nn.ConvTranspose2d(in_channels, out_channels, kernel_size=2, stride=2)] # n+1 레이어용 1
    EX_layers += [nn.Conv2d(out_channels, out_channels, kernel_size=3, stride=1, padding=1)] # n+1 레이어용 2
    EX_layers += [nn.Conv2d(out_channels, out_channels, kernel_size=3, stride=1, padding=1)] # n 레이어용 1
    EX_layers += [nn.Conv2d(out_channels, out_channels, kernel_size=3, stride=1, padding=1)] # n 레이어용 2
    return EX_layers


def add_extras(cfg, size, i, batch_norm=False):
    # Extra layers added to VGG for feature scaling
    layers = []
    SW_layers = []
    EX_layers = []
    in_channels = i
    flag = False
    for k, v in enumerate(cfg):
        if in_channels != 'S':
            if v == 'S':
                layers += [nn.Conv2d(in_channels, cfg[k + 1],
                           kernel_size=(1, 3)[flag], stride=2, padding=1)]
            else:
                layers += [nn.Conv2d(in_channels, v, kernel_size=(1, 3)[flag])]
            flag = not flag
        in_channels = v
    # SSD512 need add one more Conv layer(Conv12_2)
    if size == 512:
        layers += [nn.Conv2d(in_channels, 256, kernel_size=4, padding=1)]

    SW_layers += SW_modules(512)
    SW_layers += SW_modules(1024)
    SW_layers += SW_modules(512)

    EX_layers += Extension_modules(1024, 512)
    EX_layers += Extension_modules(512, 1024)
    EX_layers += Extension_modules(256, 512)
    EX_layers += Extension_modules(256, 256)

    return (layers, SW_layers, EX_layers)


def multibox(vgg, extra_layers_sw, cfg, num_classes):
    loc_layers = []
    conf_layers = []
    extra_layers = extra_layers_sw[0]
    vgg_source = [24, -2]
    for k, v in enumerate(vgg_source):
        loc_layers += [nn.Conv2d(vgg[v].out_channels,
                                 cfg[k] * 4, kernel_size=3, padding=1)]
        conf_layers += [nn.Conv2d(vgg[v].out_channels,
                        cfg[k] * num_classes, kernel_size=3, padding=1)]

    for k, v in enumerate(extra_layers[1::2], 2):
        loc_layers += [nn.Conv2d(v.out_channels, cfg[k]
                                 * 4, kernel_size=3, padding=1)]
        conf_layers += [nn.Conv2d(v.out_channels, cfg[k]
                                  * num_classes, kernel_size=3, padding=1)]

    return vgg, extra_layers_sw, (loc_layers, conf_layers)


base = {
    '300': [64, 64, 'M', 128, 128, 'M', 256, 256, 256, 'C', 512, 512, 512, 'M',
            512, 512, 512],
    '512': [64, 64, 'M', 128, 128, 'M', 256, 256, 256, 'C', 512, 512, 512, 'M',
            512, 512, 512],
}
extras = {
    '300': [256, 'S', 512, 128, 'S', 256, 128, 256, 128, 256],
    '512': [256, 'S', 512, 128, 'S', 256, 128, 'S', 256, 128, 'S', 256, 128],
}
mbox = {
    '300': [4, 6, 6, 6, 4, 4],  # number of boxes per feature map location
    '512': [4, 6, 6, 6, 6, 4, 4],
}


def build_ssd(phase, size=512, num_classes=21):
    if phase != "test" and phase != "train":
        print("Error: Phase not recognized")
        return
    if size != 300 and size != 512 and size != 1024:
        print("Error: Sorry only SSD300 or SSD512 is supported currently!")
        return

    # return SSD(phase, size, *multibox(vgg(base[str(size)], 3),
    #                             add_extras(extras[str(size)], size, 1024),
    #                             mbox[str(size)], num_classes), num_classes)\
    base_, extras_, head_ = multibox(vgg(base[str(size)], 3),
                                 add_extras(extras[str(size)], size, 1024),
                                 mbox[str(size)], num_classes)
    return SSD(phase, size, base_, extras_, head_, num_classes)
