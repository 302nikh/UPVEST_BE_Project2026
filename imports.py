from __future__ import annotations

import requests
import logging
import curlify
import traceback
import time
import pyotp
import copy
import json
import os
import csv
import sys
import pytz
import ast
import os
import threading
# import upstox_client
import ssl
# import websockets
import asyncio
import calendar
import shutil
import pandas as pd

from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from pprint import pprint
from dataclasses import asdict, dataclass
from urllib.parse import quote
from typing import List, Optional, Callable, Dict, Any, TYPE_CHECKING
from collections import defaultdict

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
