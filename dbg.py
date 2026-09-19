# -*- coding: utf-8 -*-
import re, glob, os, sys
sys.path.insert(0, r'c:\Users\tingting.chen\Desktop\manager_tmp')
import extract_pdf as E

d = r'c:\Users\tingting.chen\Desktop\manager_tmp\真题\01 2016-2023年11月中级历年真题合集 -1\2023年11月案例分析真题'
f = sorted(glob.glob(os.path.join(d, '*.pdf')))[int(sys.argv[1]) if len(sys.argv) > 1 else 2]
data, objs = E.load(f)
pgs = E.page_order(objs)
lines = E.extract_page(objs, pgs[0])
for l in lines[:20]:
    print(repr(l))
cs = E.content_stream(objs, pgs[0])
print('--- content head ---')
print(cs[:200])
