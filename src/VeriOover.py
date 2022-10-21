#!/usr/bin/env python3

import yaml
import os
import argparse

# import changef
import Witness
from Parser import InsertConcent
from Veri import Runclang, RunKlee, DetectError


TestPath = "/tmp/verioover/"


cnt = 0
rightnum = 0
unknow = 0
falsenum = 0
exitnum = 0


def RunVeri(filepath, spec):
    start = filepath.rfind("/") + 1
    filename = filepath[start:]

    linenumber, varscope = InsertConcent(filepath, filename)

    Runclang(filename, TestPath + filename)

    RunKlee(filename)

    flag = DetectError()

    if flag == "unknown":
        print("spec unknown!")
        return

    data_model = "LP64"

    # outpath = "./test/" + filename[:-2] + '.graphml'
    # outpath = filename[:-2] + '.graphml'
    outpath = "./witness.graphml"


    Witness.Gengraphml(flag, filepath, data_model, linenumber,varscope , outpath)

    if flag == "pass":
        print("spec correct!")
    else:
        print("spec incorrect!")


def OverflowsCheck():
    Prefix = "./sv-benchmarks-main/c/"
    NoOverflowsSet = open("./sv-benchmarks-main/c/NoOverflows-BitVectors.set")
    NoOverflowsYmlList = NoOverflowsSet.read().split('\n')[1:]

    NoOverflowsYmlList = [x for x in NoOverflowsYmlList if x != '']
    logfile = open("./test/witness.log", "w")
    global cnt
    global rightnum
    global unknow
    global falsenum
    global exitnum

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

            propertylist = []
            for p in properties:
                if len(p) >= 2:
                    propertylist.append((TarDirPath + p["property_file"], p["expected_verdict"]))
                else:
                    propertylist.append((TarDirPath + p["property_file"]))

            optionslanguage = yml["options"]["language"]

            data_model = yml["options"]["data_model"]


            # try:
            print(filepath)
            linenumber, varscope = InsertConcent(filepath, filename)
            Runclang(filename, "./test/" + filename)
            RunKlee(filename)
            flag = DetectError()

            if flag == "unknow":
                print("spec unknow!")
                unknow += 1
                print("Correct/All: {}/{}".format(rightnum, cnt))
                print("Unknow/All: {}/{}".format(unknow, cnt))
                print("false/All: {}/{}".format(falsenum, cnt))
                return

            outpath = "./test/" + filename[:-2] + '.graphml'
            Witness.Gengraphml(flag, filepath, data_model, linenumber,varscope, outpath)
            cnt += 1

            if flag == "pass":
                rightnum += 1
            else:
                falsenum += 1

            # except:
            #     logfile.write(filepath + " Verification Unknow\n")
            #     exitnum += 1

            print("Correct/All: {}/{}".format(rightnum, cnt))
            print("Unknow/All: {}/{}".format(unknow, cnt))
            print("false/All: {}/{}".format(falsenum, cnt))

    logfile.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Overflow Verifier.\n ")

    parser.add_argument("-file", type=str ,help="Input file path")
    parser.add_argument("-spec", type=str, help="Input specification path")
    parser.add_argument("-all", help="Run all Overflow Verification tasks")

    args = parser.parse_args()

    if args.all != None:
        OverflowsCheck()
    elif args.file != None and args.spec != None:
        RunVeri(args.file, args.spec)
    elif args.file == None:
        print("usage: VeriOover.py [-h] [-file FILE] [-spec SPEC] [-all ALL]")
    elif args.spec == None:
        print("usage: VeriOover.py [-h] [-file FILE] [-spec SPEC] [-all ALL]")
    else:
        pass

