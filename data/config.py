# config.py
import os.path

# gets home dir cross platform
home = os.path.expanduser("~")
ddir = os.path.join(home,"datasets/")

# note: if you used our download scripts, this should be right
VOCroot = ddir # path to VOCdevkit root dir

#SSD512 and SSD300 CONFIGS
# newer version: use additional conv12_2 layer as last layer before multibox layers
v = {
    '512': {
        'feature_maps' : [64, 32, 16, 8, 4, 2, 1],
        'deconv_feature_maps': [64, 64, 32, 16, 8, 4, 1],
        'min_dim' : 512,
        'steps' : [8, 16, 32, 64, 128, 256, 512],
        'min_sizes' : [20, 51, 133, 215, 296, 378, 460],
        'max_sizes' : [51, 133, 215, 296, 378, 460, 542],
        'aspect_ratios' : [[2], [2, 3], [2, 3], [2, 3], [2, 3], [2], [2]],
        'variance' : [0.1, 0.2],
        'clip' : True,
        'name' : 'v2_512',
    },

    '300': {
        'feature_maps': [38, 19, 10, 5, 3, 1],
        'deconv_feature_maps': [38, 38, 19, 10, 5, 1],   # 마지막은 항상 "1", deconv 를 하지 않을 것이라서
        'min_dim': 300,
        'steps': [8, 16, 32, 64, 100, 300],
        'min_sizes': [30, 60, 111, 162, 213, 264],
        'max_sizes': [60, 111, 162, 213, 264, 315],
        # 'aspect_ratios' : [[2, 1/2], [2, 1/2, 3, 1/3], [2, 1/2, 3, 1/3],
        #                    [2, 1/2, 3, 1/3], [2, 1/2], [2, 1/2]],
        'aspect_ratios': [[2], [2, 3], [2, 3], [2, 3], [2], [2]],
        'variance': [0.1, 0.2],
        'clip': True,
        'name': 'v2_300',
    },

    '1024': {
        'feature_maps_w' : [128, 64, 32, 16, 8, 4, 3],
        'feature_maps_h' : [52, 26, 13, 7, 4, 2, 1],
        'min_dim_w' : 1024,
        'min_dim_h' : 418,
        'steps_w' : [16, 32, 64, 128, 256, 512, 1024],
        'steps_h' : [6, 13, 26, 52, 104, 209, 418],
        'min_sizes' : [20, 41, 113, 185, 256, 328, 400],
        'max_sizes' : [41, 113, 185, 256, 328, 400, 472],
        # 'aspect_ratios' : [[2], [2, 3], [2, 3], [2, 3], [2, 3], [2], [2]],
        'aspect_ratios' : [[2], [2], [2], [2], [2], [2], [2]],
        'variance' : [0.1, 0.2],
        'clip' : True,
        'name' : 'v2_1024',
    },

'1025': {
        'feature_maps_w' : [128, 64, 32, 16, 8, 4, 3],
        'feature_maps_h' : [52, 26, 13, 7, 4, 2, 1],
        'min_dim_w' : 1024,
        'min_dim_h' : 418,
        'steps_w' : [16, 32, 64, 128, 256, 512, 1024],
        'steps_h' : [6, 13, 26, 52, 104, 209, 418],
        'min_sizes' : [20, 41, 113, 185, 256, 328, 400],
        'max_sizes' : [41, 113, 185, 256, 328, 400, 472],
        'aspect_ratios' : [[2], [2, 3], [2, 3], [2, 3], [2, 3], [2], [2]],
        # 'aspect_ratios' : [[2], [2], [2], [2], [2], [2], [2]],
        'variance' : [0.1, 0.2],
        'clip' : True,
        'name' : 'v2_1024',
    }
}