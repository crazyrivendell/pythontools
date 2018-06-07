#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function
from __future__ import unicode_literals

import logging
import logging.handlers
import sys
import os

LOGGING_MSG_FORMAT = "%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s"
LOGGING_DEBUG_FORMAT = "%(asctime)s %(levelname)1.1s %(filename)5.5s %(lineno)3.3s-> %(message)s"
LOGGING_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

def get_logger(logfile, path="logs/", level=logging.DEBUG, max_byte=1024*1024*50, backup_count=10):
    root_logger = logging.getLogger(logfile)
    if len(root_logger.handlers) == 0:
        if path.startswith('/'):
            if not os.path.isdir(path):
                try:
                    os.makedirs(path)
                except OSError as e:
                    print(e)
                    sys.exit(1)
            else:
                if not os.access(path, os.R_OK|os.W_OK):
                    print(path, "without read/write permission")
                    sys.exit(1)
        else:
            """ create new log file path, pwd+path """
            path = os.path.join(sys.path[0], path)
            if not os.path.isdir(path):
                os.makedirs(path)

        if not path.endswith('/'):
            path += '/'

        handler = logging.handlers.RotatingFileHandler(
                    path + logfile + ".log",
                    mode="a",
                    maxBytes=max_byte,
                    backupCount=backup_count,
                    encoding="utf-8"
                    )

        fmter1 = logging.Formatter(LOGGING_MSG_FORMAT, LOGGING_DATE_FORMAT)
        handler.setFormatter(fmter1)
        root_logger.addHandler(handler)
        root_logger.setLevel(level)

        fmter2 = logging.Formatter(LOGGING_DEBUG_FORMAT, LOGGING_DATE_FORMAT)
        console_handle = logging.StreamHandler()
        console_handle.setFormatter(fmter2)
        console_handle.setLevel(logging.DEBUG)
        root_logger.addHandler(console_handle)

    return logging.getLogger(logfile)


LOG = get_logger("LOG_TOOL", path="../logs/", level=logging.DEBUG, max_byte=1024*1024*50, backup_count=10)

def test():
    #get_logger(logfile, path="logs/", level=logging.DEBUG, max_byte=1024*1024*50, backup_count=10):
    mylog = get_logger("log_name", "abc/def", max_byte=100)
    for i in range(0, 10):
        mylog.info("%d" % i)
    for i in range(0, 10):
        LOG.info("%d" % i)

if __name__ == "__main__":
    test()
