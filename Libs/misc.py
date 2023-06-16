import tkinter as tk
from tkinter import filedialog
import cv2
from pathlib import Path
import math
import random
import json
import pandas as pd
import os
import openpyxl
import re
from tqdm import tqdm
import numpy as np
import logging
from collections import OrderedDict

logger = logging.getLogger(__name__)


def num_to_ord(input_number):
    suf = lambda n: "%d%s"%(n,{1:"st",2:"nd",3:"rd"}.get(n%100 if (n%100)<20 else n%10,"th"))
    if isinstance(input_number, list):
        return [suf(i) for i in input_number]
    elif isinstance(input_number, int):
        return suf(input_number)
    else:
        raise TypeError("Input must be an integer or a list of integers")
    
def ord_to_num(input_ord):
    if isinstance(input_ord, list):
        return [int(re.findall(r'\d+', i)[0]) for i in input_ord]
    elif isinstance(input_ord, str):
        return int(re.findall(r'\d+', input_ord)[0])
    else:
        raise TypeError("Input must be a string or a list of strings")
    
def index_to_char(input_number): # turn 0 to A
    if isinstance(input_number, list):
        return [chr(i+65) for i in input_number]
    elif isinstance(input_number, int):
        return chr(input_number+65)
    else:
        raise TypeError("Input must be an integer or a list of integers")
    
def char_to_index(input_char): # turn A to 0
    if isinstance(input_char, list):
        return [ord(i)-65 for i in input_char]
    elif isinstance(input_char, str):
        return ord(input_char)-65
