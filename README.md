# VeriOover
## Introduction

VeriOover is a verifier for detecting overflow. (C programs)



## Dependency

- Klee 2.3
- llvm 13.0.1
- pycparser 2.21
- PyYAML 6.0
- networkx 2.8.6



## Usage

```bash
usage: VeriOover [-h] [-file FILE] [-spec SPEC] [-all ALL] [--version]

Overflow Verifier.

optional arguments:
  -h, --help  show this help message and exit
  -file FILE  Input file path
  -spec SPEC  Input specification path
  -all ALL    Run all Overflow Verification tasks
  --version   VeriOover version 1.0
```

### example

```bash
./VeriOover.py -file /path/to/file -spec /path/to/specification
```



