import subprocess
import src.Witness
import os

TestPath = "/tmp/verioover/"
filedir = os.path.dirname(os.path.abspath(__file__))
clangpath = filedir + '/../bin/clang-11'
kleepath = filedir + '/../bin/klee'

import hashlib


def getsha256(path):
    f = open(path, "rb")
    sha256obj = hashlib.sha256()
    sha256obj.update(f.read())
    hash_value = sha256obj.hexdigest()
    f.close()
    return hash_value


def getarchitecture(arc):
    if arc == "LP64":
        return "64bit"
    else:
        return "32bit"


def getproducer():
    return "VeriOover"


def getspecification(specpath):
    f = open(specpath, "r")
    spec = list(filter(lambda x: True if x != "" else False, f.read().split("\n")))
    return spec[0]


def Runclang(filename, filepath):
    ctobc = subprocess.Popen([clangpath, "-I./include/",
                              "-emit-llvm",
                              "-c",
                              "-g",
                              "-O0",
                              "-Xclang",
                              "-disable-O0-optnone",
                              "-fsanitize=signed-integer-overflow",
                              filepath,
                              "-o",
                              TestPath + filename[:-2] + ".bc"])

    subprocess.Popen.wait(ctobc)


def RunKlee(filename):
    klee_ver = subprocess.Popen([kleepath,
                                 "-solver-backend=z3",
                                 "-max-time=10s",
                                 "-max-memory=7168",
                                 "-exit-on-error-type=Overflow",
                                 TestPath + filename[:-2] + ".bc"])


    subprocess.Popen.wait(klee_ver)

def DetectError():
    msgfile = open(TestPath + "/klee-last/messages.txt")
    msg = msgfile.read()


    if "overflow on" in msg:
        return "violation"
    elif "concretized symbolic size" in msg:
        return "unknow"
    elif "failed external call: __ubsan_handle_negate_overflow" in msg:
        return "violation"
    else:
        return "pass"


    # if "ERROR" in msg:
    #     exceptoutput = properties[0]
    #     if "overflow on " in msg:
    #         if exceptoutput['expected_verdict'] == False:
    #             logfile.write(inputfile + " Verification Correct\n")
    #             rightnum += 1
    #         else:
    #             logfile.write(inputfile + " Verification False\n")
    #             falsenum += 1
    #     elif "failed external call" in msg:
    #         logfile.write(inputfile + " Verification Unknow\n")
    #         unknow += 1
    #     elif exceptoutput['expected_verdict'] == False:
    #         logfile.write(inputfile + " Verification False\n")
    #         falsenum += 1
    #     else:
    #         logfile.write(inputfile + " Verification Unknow\n")
    #         unknow += 1
