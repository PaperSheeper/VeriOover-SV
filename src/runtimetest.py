#!/usr/bin/env python3

import subprocess
import os
import yaml
import re
from VeriOover import RunVeri
import time


Prefix = "./sv-benchmarks-main/c/"

TestPath = "./test/"
# NoOverflowsSet = open("./sv-benchmarks-main/c/NoOverflows-BitVectors.set")

NoOverflowsSet = open("./sv-benchmarks-main/c/NoOverflows-Other.set")

NoOverflowsYmlList = NoOverflowsSet.read().split('\n')[1:]

NoOverflowsYmlList = [x for x in NoOverflowsYmlList if x != '']
spec = "CHECK( init(main()), LTL(G ! overflow) )"


for i in NoOverflowsYmlList:
    TarDirPath = Prefix + i[:-5]
    print("Now Path: ", TarDirPath)
    TarDir = os.listdir(TarDirPath)
    TarYmlList = [x for x in TarDir if x[-3:] == "yml"]
    for ymlfile in TarYmlList:
        yf = open(TarDirPath + ymlfile)
        yml = yaml.load(yf, Loader=yaml.FullLoader)
        filename = yml["input_files"]
        filepath = TarDirPath + yml["input_files"]
        properties = yml["properties"]

        # print(filepath)
        # print(filename)

        f = open("./debug/time.log", "a")

        f.write("[debug] " + filepath + ": ")
        f.close()

        # verproc = os.popen("/usr/bin/time  -a -o time.log ./VeriOover.py " +
        #                             " -file " +
        #                             filepath +
        #                             " -spec " +
        #                             " ./no-overflow.prp "
        # )
        #
        # print(verproc.read())


        verproc = subprocess.call(["/usr/bin/time", "-a" , "-o", "./debug/time.log",
                          "./VeriOover.py",
                          "-file",
                          filepath,
                          "-spec",
                          "./no-overflow.prp"
        ])



        # print(lst)