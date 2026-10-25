import sys
OUT = sys.argv[1].rstrip('/') + '/'  # archive change: output folder (was hard-coded)
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyBboxPatch, FancyArrowPatch
import html

W, H = 7.75, 6.0
fig, ax = plt.subplots(figsize=(W, H)); ax.set_xlim(0, W); ax.set_ylim(0, H); ax.axis("off")
font = "DejaVu Sans"
col = {"none":"#E7ECEF","static":"#F6D7A7","ctrl":"#D9D2E9","c":"#BFE3C8","d":"#F4C7C3","e":"#C9DDF2"}
arms = [
 ("A  Frozen clean", "none", "Clean fit\n(5 epochs)", "none", "Attack current model\nNo update"),
 ("B  Static adversarial", "static", "Clean fit, then 5 epochs\n+ 500 adversarial\nexamples", "static", "Attack current model\nNo update"),
 ("C  Incremental\n+ rehearsal", "none", "Clean fit\n(5 epochs)", "c", "Attack, then update on\nevasions + 1,000\nclean memory"),
 ("D  Incremental,\nno rehearsal", "none", "Clean fit\n(5 epochs)", "d", "Attack, then update on\nevasions only"),
 ("E  Balanced replay,\nlow learning rate", "none", "Clean fit\n(5 epochs)", "e", "Attack, then update on\nevasions + 500/500\nreplay, lr 0.0002"),
 ("F  Clean-continued\ncontrol", "ctrl", "Clean fit, then 5 more\nclean epochs", "ctrl", "Attack current model\nNo update"),
]
x0=0.08; labw=1.62; gapx=0.05
cols = [("Before round 1",1.65), ("Rounds 1 to 5 (repeated)",2.25), ("Evaluation\nafter every round",1.7)]
xs=[]; xx=x0+labw+gapx
for n,w in cols: xs.append((xx,w)); xx+=w+gapx
top=5.15; rh=0.56; hh=0.46
heads=["#2F3E4E","#2F3E4E","#8A2D2D"]
for (cx,w),(n,_),c in zip(xs,cols,heads):
    ax.add_patch(Rectangle((cx,top+0.04),w,hh,fc=c,ec="none"))
    ax.text(cx+w/2,top+0.04+hh/2,n,ha="center",va="center",color="white",fontsize=7.6,fontweight="bold",family=font)
ytop=[]
for r,(lab,k0,t0,k1,t1) in enumerate(arms):
    y=top-(r+1)*(rh+0.05)+0.05; ytop.append(y)
    ax.add_patch(Rectangle((x0,y),labw,rh,fc="#F4F6F8",ec="#9AA5B1",lw=0.7))
    ax.text(x0+0.07,y+rh/2,lab,ha="left",va="center",fontsize=7.2,fontweight="bold",family=font,linespacing=1.15)
    ax.add_patch(Rectangle((xs[0][0],y),xs[0][1],rh,fc=col[k0],ec="#9AA5B1",lw=0.7))
    ax.text(xs[0][0]+xs[0][1]/2,y+rh/2,t0,ha="center",va="center",fontsize=6.6,family=font,linespacing=1.15)
    ax.add_patch(Rectangle((xs[1][0],y),xs[1][1],rh,fc=col[k1],ec="#9AA5B1",lw=0.7))
    ax.text(xs[1][0]+xs[1][1]/2,y+rh/2,t1,ha="center",va="center",fontsize=6.6,family=font,linespacing=1.15)
    ax.add_patch(Rectangle((xs[2][0],y),xs[2][1],rh,fc="#FBF3F3",ec="#9AA5B1",lw=0.7))
    ax.text(xs[2][0]+xs[2][1]/2,y+rh/2,"Fresh attack on the\ncurrent model, plus\nclean test metrics",ha="center",va="center",fontsize=6.6,family=font,linespacing=1.15)
# bottom explanatory panel
yb=top-6*(rh+0.05)-0.02
ax.add_patch(FancyBboxPatch((x0,0.06),xx-x0-gapx-0.0,yb-0.10,boxstyle="round,pad=0.01,rounding_size=0.05",fc="#FAFAF7",ec="#9AA5B1",lw=0.7))
blocks=[("Data (per seed)","Official training partition\n(175,341 records) split 70/15/15\nby class: initial training 122,738,\nvalidation 26,301, adaptation\nstream 26,302 (five round slices).\nOfficial test (82,332): evaluation\nonly."),
        ("Each round, all six arms","100 malicious flows are drawn from\nthe round's slice. Each arm's\ncurrent model is attacked at the\ncommon fixed threshold. Successful\nevasions become simulated labels.\nOnly C, D and E update."),
        ("Evaluation (sealed test set)","Up to 1,000 malicious test flows\nthat the initial model detects are\nattacked afresh. Each arm uses its\nown validation-calibrated\nthreshold (at most 5% validation\nFPR). Test FPR is measured\nseparately.")]
bw=(xx-x0-gapx-0.3)/3
for k,(h,b) in enumerate(blocks):
    bx=x0+0.1+k*(bw+0.05)
    ax.text(bx,yb-0.07,h,ha="left",va="top",fontsize=7.1,fontweight="bold",family=font)
    ax.text(bx,yb-0.27,b,ha="left",va="top",fontsize=6.2,family=font,linespacing=1.25)
fig.savefig(OUT+"fig1_experiment_map.png",dpi=300,bbox_inches="tight",facecolor="white")
fig.savefig(OUT+"fig1_experiment_map.svg",bbox_inches="tight",facecolor="white")

# ---- draw.io source ----
S=100
def px(v): return int(round(v*S))
cells=[]; cid=[2]
def box(x,y,w,h,text,fill="#FFFFFF",stroke="#9AA5B1",fc="#000000",bold=False,size=10,align="center"):
    i=cid[0]; cid[0]+=1
    st=f"rounded=0;whiteSpace=wrap;html=1;fillColor={fill};strokeColor={stroke};fontColor={fc};fontSize={size};align={align};verticalAlign=middle;"+("fontStyle=1;" if bold else "")
    cells.append(f'<mxCell id="{i}" value="{html.escape(text.replace(chr(10)," "),quote=True)}" style="{st}" vertex="1" parent="1"><mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry"/></mxCell>')
def Y(y,h): return px(H-(y+h))
for (cx,w),(n,_),c in zip(xs,cols,heads):
    box(px(cx),Y(top+0.04,hh),px(w),px(hh),n,c,c,"#FFFFFF",True,11)
for r,(lab,k0,t0,k1,t1) in enumerate(arms):
    y=ytop[r]
    box(px(x0),Y(y,rh),px(labw),px(rh),lab,"#F4F6F8",bold=True,size=11,align="left")
    box(px(xs[0][0]),Y(y,rh),px(xs[0][1]),px(rh),t0,col[k0],size=10)
    box(px(xs[1][0]),Y(y,rh),px(xs[1][1]),px(rh),t1,col[k1],size=10)
    box(px(xs[2][0]),Y(y,rh),px(xs[2][1]),px(rh),"Fresh attack on the current model, plus clean test metrics","#FBF3F3",size=10)
for k,(h,b) in enumerate(blocks):
    bx=x0+0.05+k*(bw+0.1)
    box(px(bx),Y(0.06,yb-0.10),px(bw+0.05),px(yb-0.10),h+" - "+b,"#FAFAF7",size=10,align="left")
xml='<mxfile host="app.diagrams.net"><diagram name="Fig1 experiment map"><mxGraphModel dx="900" dy="700" grid="1" gridSize="10" page="1" pageWidth="%d" pageHeight="%d"><root><mxCell id="0"/><mxCell id="1" parent="0"/>%s</root></mxGraphModel></diagram></mxfile>'%(px(W)+40,px(H)+40,"".join(cells))
open(OUT+"fig1_experiment_map.drawio","w").write(xml)
