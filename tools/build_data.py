import csv, json, re, sys
# 用法：python3 tools/build_data.py data/ILEPB04004.csv 2025-06-20
# 讀入環保局清運點 CSV，整理後嵌入 template.html，輸出 index.html
import os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src = sys.argv[1]
version = sys.argv[2] if len(sys.argv) > 2 else '未標示'
CN = {'一':1,'二':2,'三':3,'四':4,'五':5,'六':6,'日':7,'天':7}
rows=[]
with open(src, encoding='utf-8-sig') as f:
    r = csv.reader(f); hdr = next(r)
    for rec in r:
        if len(rec)!=9: continue
        day,town,seq,tm,car,route,name,lat,lon = rec
        if '石板橋頭' in lon and name=='福德廟':   # malformed source row: name split by comma, lat/lon shifted
            name = '福德廟、石板橋頭(星期三、六停收)'; lat, lon = '24.782311', lat
        rows.append(dict(day=int(day),town=town.replace('清潔隊',''),seq=int(seq),tm=tm,car=car,route=route,name=name,lat=float(lat),lon=float(lon)))
def parse(name):
    allowed=set(range(1,8)); note=[]
    parts = re.findall(r'[（(]([^()（）]*)[)）]', name)
    clean = re.sub(r'[（(](星期三、六停收|[^()（）]*行駛|[^()（）]*停駛)[)）]','',name).strip()
    for p in parts:
        if '停收' in p: continue
        if p.endswith('行駛'):
            ds={CN[c] for c in p if c in CN}
            if ds: allowed &= ds; note.append(p)
        elif '寒、暑假停駛' in p: note.append('寒暑假停駛')
        elif p.endswith('停駛'):
            ds={CN[c] for c in p if c in CN}; allowed -= ds; note.append(p)
    allowed -= {3,6}   # 全縣週三、週六停收
    return clean, allowed, '、'.join(note)
towns=[]; routes=[]; rkey={}; entries={}
for x in rows:
    if x['town'] not in towns: towns.append(x['town'])
    k=(x['town'],x['route'])
    if k not in rkey:
        rkey[k]=len(routes); routes.append([towns.index(x['town']), re.sub(r'^'+x['town'],'',x['route']) or x['route'], x['car']])
    clean, allowed, note = parse(x['name'])
    h,m = map(int,x['tm'].split(':'))
    ek=(rkey[k],x['seq'],h*60+m,clean,round(x['lat'],6),round(x['lon'],6),note)
    e = entries.setdefault(ek, {'days':set(),'allowed':allowed})
    e['days'].add(x['day'])
S=[]
for (ri,seq,mins,clean,lat,lon,note),e in entries.items():
    days = e['days'] & e['allowed']
    if not days: continue
    mask = sum(1<<(d-1) for d in days)
    S.append([ri,seq,mins,clean,int(round(lat*1e5)),int(round(lon*1e5)),mask,note])
S.sort(key=lambda s:(s[0],s[1],s[2]))
data={'towns':towns,'routes':routes,'stops':S,'updated':version}
blob = json.dumps(data, ensure_ascii=False, separators=(',',':')).replace('</','<\\/')
tpl = open(os.path.join(ROOT,'template.html'),encoding='utf-8').read()
open(os.path.join(ROOT,'index.html'),'w',encoding='utf-8').write(tpl.replace('__DATA__', blob))
print('鄉鎮市', len(towns), '路線', len(routes), '清運紀錄', len(S), '→ index.html 已更新')
