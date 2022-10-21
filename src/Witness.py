import hashlib
import lib.networkx as nx
import os
import subprocess
import re

TestPath = "/tmp/verioover/"
filedir = os.path.dirname(os.path.abspath(__file__))
ktestpath = filedir + '/../bin/ktest-tool '

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
    spec = list(filter(lambda x : True if x != "" else False, f.read().split("\n")))
    return spec[0]



# witness-type = "witness-type"
# sourcecodelang = "C"
# producer = Witness.getproducer()
# spec = "CHECK( init(main()), LTL(G ! overflow) )"
# programfile = filepath
# sha256 = Witness.getsha256(filepath)
# architecture = Witness.getarchitecture(data_model)

def addwitness_type(G, witness_type):
    G.graph['witness-type'] = witness_type

def addsourcecodelang(G, sourcecodelang):
    G.graph['sourcecodelang'] = sourcecodelang

def addproducer(G, producer):
    G.graph['producer'] = producer

def addspec(G, spec):
    G.graph['specification'] = spec

def addprogramfile(G, programfile):
    G.graph['programfile'] = programfile

def addsha256(G, sha256):
    G.graph['programhash'] = sha256

def addarchitecture(G, arch):
    G.graph['architecture'] = arch

def NetGraph():
    G = nx.DiGraph()
    return G


def addnodedata(G, id, key, value, ):
    G.add_node(id)
    G.nodes[id][key] = value

def addnode(G, id):
    G.add_node(id)

def addedgedata(G, src, tar, startline, originfile, assumption, scope):
    G.add_edge(src, tar)
    G[src][tar]["startline"] = startline
    G[src][tar]["originfile"] = originfile
    G[src][tar]["assumption"] = assumption
    G[src][tar]["assumption.scope"] = scope

def addedge(G, src, tar):
    G.add_edge(src, tar)



def Finderror(path):
    objnum = 0
    dirlist = os.listdir(path)
    idmap = []
    targetfile = ""
    for i in dirlist:
        if i[-12:] == "overflow.err":
            targetfile = i[:10] + '.ktest'
            break
        elif i[-12:] == "external.err":
            targetfile = i[:10] + '.ktest'
            break

    r = os.popen(ktestpath + path+targetfile)
    klist = r.read().split('\n')

    i = 0
    while i < len(klist):
        if "num objects:" in klist[i]:
            start = klist[i].rfind(" ")
            objnum = int(klist[i][start:])
            i += 1
            continue

        if "name" in klist[i]:
            start = klist[i].find('\'')
            idname = klist[i][start+1:-1]
            # print(idname)
            i += 4
            start = klist[i].find("int :") + 5
            idval = klist[i][start:]
            idmap.append((idname, idval))
            continue
        i += 1

    return idmap, objnum



def Gengraphml(flag, filepath, data_model, linenumber, varscope, outpath):
    G = NetGraph()

    nodeid = 0

    if flag == "pass":
        witness_type = "correctness_witness"
        sourcecodelang = "C"
        producer = getproducer()
        spec = "CHECK( init(main()), LTL(G ! overflow) )"
        programfile = filepath
        sha256 = getsha256(filepath)
        architecture = getarchitecture(data_model)

        addwitness_type(G, witness_type)
        addsourcecodelang(G, sourcecodelang)
        addproducer(G, producer)
        addspec(G, spec)
        addprogramfile(G, programfile)
        addsha256(G, sha256)
        addarchitecture(G, architecture)

        addnodedata(G, nodeid, "entry", "true")
        # outpath_1= "/home/jucico/sv/VeriOover-main/correct_witness/"+outpath[:-8][7:]+'.graphml'
        # sname = outpath.rfind("/")
        # outpath = outpath[:sname+1] + "True_" + outpath[sname+1:]
        nx.write_graphml(G, outpath, named_key_ids=True)

    else:
        witness_type = "violation_witness"
        sourcecodelang = "C"
        producer = getproducer()
        spec = "CHECK( init(main()), LTL(G ! overflow) )"
        programfile = filepath
        sha256 = getsha256(filepath)
        architecture = getarchitecture(data_model)

        addwitness_type(G, witness_type)
        addsourcecodelang(G, sourcecodelang)
        addproducer(G, producer)
        addspec(G, spec)
        addprogramfile(G, programfile)
        addsha256(G, sha256)
        addarchitecture(G, architecture)

        idmap, objnum = Finderror(TestPath + "/klee-last/")

        addnodedata(G, nodeid, "entry", "true")
        nodeid += 1
        # print(linenumber)
        # print(idmap)
        for idname, idval in idmap:
            r1 = r"symbolic-"
            if not (re.search(r1, idname)):
                addnode(G, nodeid)
                addedgedata(G, nodeid - 1, nodeid, linenumber[idname], filepath, idname + "==" + idval, varscope[idname])
                nodeid += 1

        # nx.write_graphml(G, "witness.graphml", named_key_ids=True)

        addnodedata(G, nodeid, "violation", "true")
        addedge(G, nodeid-1, nodeid)

        # sname = outpath.rfind("/")
        # outpath = outpath[:sname+1] + "False_" + outpath[sname+1:]

        nx.write_graphml(G, outpath, named_key_ids=True)
