import re,json
from shapely.geometry import Polygon, MultiPolygon
from shapely.ops import unary_union
from shapely.geometry.polygon import orient
s=open('beotkkotnangsi-site/index.html',encoding='utf-8').read()
m=re.search(r'const PATHS=(\{.*?\});\n',s); P=json.loads(m.group(1))
def poly(d):
    pts=[tuple(map(float,p.split(','))) for p in re.findall(r'-?[\d.]+,-?[\d.]+',d)]
    return Polygon(pts).buffer(0)
G={"경기도":["경기도","인천광역시"],"대전광역시":["대전광역시","세종특별자치시","충청북도","충청남도"],
"대구광역시":["대구광역시","경상북도"],"광주광역시":["광주광역시","전라남도","전라북도"],
"부산광역시":["부산광역시","경상남도","울산광역시"],"강원도":["강원도"],"제주특별자치도":["제주특별자치도"],"서울특별시":["서울특별시"]}
R=1.6
land=unary_union([poly(v['d']).buffer(R,join_style=2) for v in P.values()]).buffer(-R,join_style=2)
order=["서울특별시","제주특별자치도","강원도","경기도","대전광역시","대구광역시","부산광역시","광주광역시"]
taken=None; out={}
for k in order:
    g=unary_union([poly(P[n]['d']) for n in G[k]]).buffer(R,join_style=2).buffer(-R,join_style=2)  # close inner seams
    g=g.buffer(R*1.2,join_style=2).intersection(land) if k!="서울특별시" else g
    if taken is not None: g=g.difference(taken)
    g=g.buffer(0)
    # drop crumbs
    parts=[q for q in (g.geoms if hasattr(g,'geoms') else [g]) if q.area>4]
    g=MultiPolygon(parts) if len(parts)>1 else parts[0]
    taken=g if taken is None else unary_union([taken,g])
    def ring(c): 
        c=list(c)[:-1]; return 'M'+' '.join(f'{x:.1f},{y:.1f}' for x,y in c)+'Z'
    d=''
    for q in (g.geoms if hasattr(g,'geoms') else [g]):
        q=orient(q.simplify(0.15),1.0); d+=ring(q.exterior.coords)+''.join(ring(i.coords) for i in q.interiors)
    ms=[P[n] for n in G[k]]; A=[poly(x['d']).area for x in ms]
    cx=sum(x['cx']*a for x,a in zip(ms,A))/sum(A); cy=sum(x['cy']*a for x,a in zip(ms,A))/sum(A)
    out[k]={"d":d,"cx":round(cx,1),"cy":round(cy,1),"parts":len(parts)}
    print(k,len(parts),round(g.area))
# gap check
allr=unary_union([poly(o['d']) if False else None for o in []] or [taken])
print('uncovered land',round(land.difference(taken).area,2))
json.dump({k:{"d":v["d"],"cx":v["cx"],"cy":v["cy"]} for k,v in out.items()},open('rpaths.json','w'),ensure_ascii=False)
