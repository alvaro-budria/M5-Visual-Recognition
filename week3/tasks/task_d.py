import json
from pathlib import Path
import numpy as np
import pandas as pd
import cv2
from PIL import Image
import torch

from detectron2 import model_zoo
from detectron2.config import get_cfg
from detectron2.data import MetadataCatalog
from detectron2.engine import DefaultPredictor
from detectron2.utils.visualizer import Visualizer

MODELS = {
    "mask": 'COCO-InstanceSegmentation/mask_rcnn_R_50_FPN_3x.yaml',
    "faster": 'COCO-Detection/faster_rcnn_R_50_FPN_3x.yaml',
}

MODEL = MODELS['mask']
device = 'cuda'

def task_d(*args, attacked_image = './data/weird/el_bone.jpg'):

    npimage = cv2.imread(attacked_image)
    npimage = cv2.resize(npimage, (224, int(224 * npimage.shape[0]/npimage.shape[1]) ))
    image = torch.from_numpy(npimage.transpose(2, 0, 1)).float().to(device)

    cfg = get_cfg()
    cfg.merge_from_file(model_zoo.get_config_file(MODEL))
    cfg.MODEL.WEIGHTS = model_zoo.get_checkpoint_url(MODEL)
    cfg.MODEL.ROI_HEADS.SCORE_THRESH_TEST = 0.5

    # Normalize the input image
    mean = torch.tensor(cfg.MODEL.PIXEL_MEAN).view(3, 1, 1).to(device)
    std = torch.tensor(cfg.MODEL.PIXEL_STD).view(3, 1, 1).to(device)
    tensor_image = (image - mean) / std


    predictor = DefaultPredictor(cfg)
    model = predictor.model

    epsilon = 0.01
    tensor_image.requires_grad = True
    output = model([{'image': tensor_image}])
    logits = output[0]['instances'].scores

    target = torch.tensor([[0]]).to(device)  # the target class index (set to 0 for simplicity)
    print(logits.shape, target.shape)
    loss = torch.nn.functional.cross_entropy(logits, target)
    loss.backward()

        # Use the sign of the gradients to generate the perturbation
    perturbation = epsilon * torch.sign(tensor_image.grad)

    # Add the perturbation to the original image to create the adversarial example
    adversarial_image = image + perturbation.detach().numpy()

    # Ensure that the adversarial image is within the valid range of values (0 to 1)
    adversarial_image = np.clip(adversarial_image, 0, 1)

    print(adversarial_image)

if __name__ == '__main__': 
    task_d()