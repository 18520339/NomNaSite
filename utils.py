import os
import cv2
import shutil
import numpy as np
import streamlit as st
from urllib.request import urlretrieve
from crnn import CRNN
from dbnet import DBNet


@st.cache
def download_assets():
    if not os.path.exists('assets.zip'):
        urlretrieve('https://nomnaftp.000webhostapp.com/assets.zip', 'assets.zip')
    if not os.path.exists('assets'):
        shutil.unpack_archive('assets.zip', 'assets')


@st.cache(hash_funcs={DBNet: lambda _: None, CRNN: lambda _: None})
def load_models():
    det_model = DBNet()
    reg_model = CRNN()
    det_model.model.load_weights('./assets/DBNet.h5')
    reg_model.model.load_weights('./assets/CRNN.h5')
    return det_model, reg_model


def order_points_clockwise(box_points):
    points = np.array(box_points)
    s = points.sum(axis=1)
    diff = np.diff(points, axis=1)
    quad_box = np.zeros((4, 2), dtype=np.float32)
    quad_box[0] = points[np.argmin(s)]
    quad_box[2] = points[np.argmax(s)]
    quad_box[1] = points[np.argmin(diff)]
    quad_box[3] = points[np.argmax(diff)]
    return quad_box


def get_patch(page, points):
    points = order_points_clockwise(points)
    page_crop_width = int(max(
        np.linalg.norm(points[0] - points[1]),
        np.linalg.norm(points[2] - points[3]))
    )
    page_crop_height = int(max(
        np.linalg.norm(points[0] - points[3]),
        np.linalg.norm(points[1] - points[2]))
    )
    pts_std = np.float32([
        [0, 0], [page_crop_width, 0], 
        [page_crop_width, page_crop_height],[0, page_crop_height]
    ])
    M = cv2.getPerspectiveTransform(points, pts_std)
    return cv2.warpPerspective(
        page, M, (page_crop_width, page_crop_height), 
        borderMode=cv2.BORDER_REPLICATE, flags=cv2.INTER_CUBIC
    )