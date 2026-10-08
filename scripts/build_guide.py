"""Build the illustrated HDB Atlas guide. Documentation dependencies: reportlab, Pillow."""
from pathlib import Path
from datetime import date
import sys
from xml.sax.saxutils import escape
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor, white
from reportlab.lib.pagesizes import A4
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle
from PIL import Image
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from backend.data import connect, metadata, dashboard

ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'output/pdf/HDB-Atlas-Guide.pdf'
OUT.parent.mkdir(parents=True,exist_ok=True)
W,H=A4
M=44
CW=W-2*M
INK=HexColor('#152238');MUTED=HexColor('#56667b');CYAN=HexColor('#067e79');PINK=HexColor('#b53180');DARK=HexColor('#0c111d')
c=canvas.Canvas(str(OUT),pagesize=A4)
c.setTitle('HDB Atlas | User and project guide')
c.setAuthor('HDB Atlas project')
c.setSubject('Dashboard guide, methodology, setup and maintenance')
with connect() as con:
    meta=metadata(con)
    summary=dashboard(con,{'start':'2025-11','end':'2026-10'})['summary']


def para(text,y,size=10.5,color=INK,width=CW,leading=15):
    style=ParagraphStyle('body',fontName='Helvetica',fontSize=size,leading=leading,textColor=color)
    p=Paragraph(text,style);_,height=p.wrap(width,H)
    if y-height < 55: raise ValueError(f"Page {c.getPageNumber()} content exceeds footer: {text[:70]}")
    p.drawOn(c,M,y-height)
    return y-height-10


def header(num,kicker,title,subtitle=None):
    c.setFillColor(white);c.rect(0,0,W,H,fill=1,stroke=0)
    c.setFillColor(CYAN);c.rect(M,H-39,27,3,fill=1,stroke=0)
    c.setFont('Helvetica-Bold',8);c.drawString(M+37,H-39,'HDB / ATLAS')
    c.setFillColor(MUTED);c.setFont('Helvetica',8);c.drawRightString(W-M,H-39,kicker.upper())
    c.setStrokeColor(HexColor('#dce3eb'));c.line(M,43,W-M,43)
    c.setFillColor(MUTED);c.setFont('Helvetica',8);c.drawString(M,28,'HDB Atlas  |  Historical resale intelligence')
    c.drawRightString(W-M,28,f'{num:02d} / 09')
    y=H-88
    y=para(title,y,25,INK,leading=30)
    if subtitle:y=para(subtitle,y,10.5,MUTED)
    return y-9


def section(title,y):
    return para(title,y,13,CYAN,leading=18)


def shot(name,y,caption,caption_color=MUTED):
    path=ROOT/'docs/screenshots'/name
    with Image.open(path) as im: iw,ih=im.size
    height=min(CW*ih/iw,310)
    width=height*iw/ih
    c.drawImage(str(path),M+(CW-width)/2,y-height,width=width,height=height,preserveAspectRatio=True)
    y-=height+9
    return para(caption,y,8,caption_color,leading=11)-5


def bullets(items,y):
    for item in items:y=para('&#8226; '+item,y,10.5,leading=15)
    return y


def code(lines,y):
    height=len(lines)*17+20
    c.setFillColor(DARK);c.roundRect(M,y-height,CW,height,5,fill=1,stroke=0)
    c.setFillColor(HexColor('#72e7d4'));c.setFont('Courier',10)
    for i,line in enumerate(lines):c.drawString(M+15,y-21-i*17,line)
    return y-height-16


def table(headers,rows,widths,y):
    rowh=29
    c.setFillColor(DARK);c.rect(M,y-rowh,CW,rowh,fill=1,stroke=0)
    x=M
    for text,w in zip(headers,widths):
        c.setFillColor(white);c.setFont('Helvetica-Bold',9);c.drawString(x+10,y-18,text);x+=w
    y-=rowh
    for idx,row in enumerate(rows):
        c.setFillColor(HexColor('#f0f5f7') if idx%2==0 else white);c.rect(M,y-rowh,CW,rowh,fill=1,stroke=0)
        x=M
        for text,w in zip(row,widths):
            c.setFillColor(INK);c.setFont('Helvetica',9);c.drawString(x+10,y-18,str(text));x+=w
        y-=rowh
    return y-18

# 1: Overview

y=header(1,'User and project guide','HDB / ATLAS','Current documentation snapshot: 8 October 2026. Explore prices, neighbourhood context and the evidence behind an asking price.')
y=shot('overview.jpg',y,'November 2025 - October 2026; all towns and flat types. Actual browser capture.')
y=section('One app, several questions',y)
y=bullets(['Explore 988,123 completed resale records from January 1990 through October 2026. The latest month may be incomplete.','Compare town medians, trends, flat types and individual transactions; explore 17 geographic overlays and 11 reference datasets.','Rank eligible secondary schools by supplied programme breadth and recorded station access. Compare national and estate price equations.','Enter an asking price, estate, flat type and remaining lease to see a comparable-sale range and whether the price is supported.'],y)
y=para('<b>Reading route:</b> map (2), charts (3), transactions (4), schools (5), asking prices (6), equations (7), methodology (8), setup and maintenance (9).',y)
y=para('The app describes historical evidence. It does not establish academic quality, causal amenity premiums, or the probability that a particular flat will sell.',y,10,MUTED)
c.showPage()

# 2: Map
y=header(2,'Explore / geography','One island. Many markets.','Compare historical transactions, then inspect the records behind each aggregate.')
y=shot('map.jpg',y,'Latest 12-month view. OpenStreetMap and URA attribution is retained.')
y=bullets(['Colour represents median resale price or median price per square metre. Marker size represents transaction volume.','Selecting a town updates the summary, trend, flat profile and transaction table. Map and ranking comparisons remain island-wide for the selected dates and flat type.','Choose a Map overlay for MRT exits, hawker centres, parks, cycling paths, school zones and other source geography. One layer is shown at a time.','Pan and zoom to load the visible area. Large overlays are capped at 2,000 displayed features; zoom in when a limit is reported.'],y)
y=section('Geography has limits',y)
y=para('Markers are planning-area centroids, not geocoded HDB blocks. Boundaries provide context, not exact HDB town boundaries. School road zones are not admission boundaries. Reference layers have their own snapshot dates.',y)
c.showPage()

# 3: Analytics
y=header(3,'Explore / analysis','Follow the signal.','Compare similar homes before interpreting differences in price.')
y=shot('analytics.jpg',y,'Price trend, flat-type mix and town rankings: November 2025 - October 2026.')
y=bullets(['From and To are inclusive month filters. Reset selects the latest 12 available months, all towns and flat types. Shared filters are preserved in the URL.','Trend modes show monthly median price, median price per square metre, or transaction volume. Zero-sale months remain visible, without a price median.','Flat profile starts with transaction shares. Compare prices shows median prices by type. Town rankings use the map price measure.'],y)
y=para(f'<b>Captured window:</b> {summary["count"]:,} sales; median price SGD {summary["price"]:,.0f}; median area {summary["area"]:g} square metres. Values reflect the imported snapshot, not live listings.',y)
y=para('Median changes can reflect the homes sold, including size, age and location. They are not a quality-adjusted appreciation index.',y,10,MUTED)
c.showPage()

# 4: Transactions
y=header(4,'Explore / records','Every sale has a story.','Trace aggregate patterns to source records.')
y=shot('transactions.jpg',y,'Current transaction explorer, with 12 records per page and current-page CSV export.')
y=bullets(['Search a block or street. Search affects the table only; shared date, town and flat-type filters still apply.','Rows are ordered by month descending, then import ID. The source does not give the order of sales within a month.','Export page downloads only the displayed page. The 13-column CSV includes the source filename.','Search resets pagination; shared-filter changes reset the table. Search and page are not included in shared URLs.'],y)
y=para('Remaining lease is displayed when supplied. Missing historical leases stay missing. Duplicate-looking records are preserved because they may represent distinct sales.',y)
c.showPage()

# 5: Schools
y=header(5,'Explore / neighbourhood','Programmes and access.','Use the supplied reference data to explore everyday convenience and school options.')
y=shot('schools.jpg',y,'Balanced ranking of 115 eligible secondary schools; source-recorded travel times.')
y=bullets(['The score balances 50% station access, 25% unique subject listings and 25% CCA choices. Each school is compared across the same 189 station origins.','Lower median source-recorded travel time improves the access component. The source does not specify mode or departure time: these are not walking times from a flat.','School profiles link subjects, CCAs, MOE and distinctive programmes. Other reference views cover HDB buildings, markets and transport/community statistics.'],y)
y=para('This ranking is not academic performance, school quality or an admissions forecast. Incomplete or conflicting matches are excluded. School and transport convenience may affect daily life, but these data do not quantify a causal resale premium.',y,10,MUTED)
c.showPage()

# 6: Asking prices
y=header(6,'Assess / asking price','Is the asking price supported?','A four-input comparison of asking price with recorded completed sales.')
y=shot('asking-price.jpg',y,'Jurong East, five-room, 54 years remaining, SGD 679,999 asking. Actual form result.')
y=para('<b>Result:</b> the indicative range is <b>SGD 610,000-685,000</b>, based on 57 sales across 34 blocks. The median is SGD 648,000. Asking is within the range, 4.9% above the median.',y)
y=bullets(['Match the same estate and flat type, with supplied remaining lease within five years. Use the 12 months before the latest source month.','The range is the 25th-75th percentile of matched prices. At least 20 sales across three blocks are required; otherwise no verdict or range is issued.','Above the upper endpoint: below asking is better supported. Within or below the range: at asking is supported by comparable prices.'],y)
y=para('<b>Limits:</b> this is a historical benchmark, not a predicted sale-price interval. Size, floor, condition and exact location are not controlled for. Unsold listings and matched asking-price histories are absent, so sale likelihood and time to sale are not estimated.',y,10,MUTED)
c.showPage()

# 7: Equations
y=header(7,'Compare / price equations','What anchors each estate?','Compare one national specification with separately fitted estate relationships.')
y=shot('price-equations.jpg',y,'Singapore and Jurong East equations, with sample sizes and chronological test errors.')
y=para('Models explain log price using floor area, flat type, remaining lease, storey, timing and, nationally, estate effects. The current training window is October 2023-March 2026; testing uses April-September 2026. The latest source month is excluded.',y)
y=bullets(['The current artifact contains 25 independent estate models. Bukit Timah uses national slopes plus an estate adjustment because its sample is too small.','Compare local and national errors on the same later sales. National mean absolute percentage error is 9.8%; this is not an individual prediction interval.','Factor-removal bars show the increase in held-out error when a group is removed and refitted. Negative bars mean removal helped on that test period.'],y)
y=para('Different housing mixes and lease ranges affect the relationships each model can learn. Coefficient intervals are not valuation ranges; estate effects cannot be assigned specifically to schools or MRT access. The asking-price form uses a separate comparable-sales method.',y,10,MUTED)
c.showPage()

# 8: Methodology
y=header(8,'Reference / data','Know your data.','Exact calculations, source coverage and reuse terms.')
y=table(['Period','Rows','Date basis'],[('1990-1999','287,196','Approval'),('2000-Feb 2012','369,651','Approval'),('Mar 2012-Dec 2014','52,203','Registration'),('2015-2016','37,153','Registration'),('2017-Oct 2026','241,920','Registration'),('TOTAL',f'{meta["count"]:,}','Five resale CSVs')],[220,110,CW-330],y)
y=section('Calculate from individual records',y)
y=para('Median price is calculated from matching sale prices. Price per square metre is calculated for each transaction before taking its median. Median area is calculated independently. Subgroup medians are never averaged. Prices are nominal SGD, without inflation adjustment.',y)
y=section('Snapshot and matching limits',y)
y=para('There is no automatic refresh or listing-site monitoring. Approval dates change to registration dates in March 2012. Reference datasets have separate dates and definitions. Source-recorded accessibility is not a live route from a home.',y)
y=section('Attribution and licence',y)
y=para('Original code and documentation: MIT License, copyright 2026 Randhir Prem (randhirprem). Third-party data, maps, fonts and dependencies retain their respective licences. Inclusion does not relicense them under MIT.',y)
y=para('Local boundaries: <link href="https://data.gov.sg/datasets/d_4765db0e87b9c86336792efe8a1f7a66/view" color="#067e79">URA Master Plan 2019 planning areas</link>, under the Singapore Open Data Licence. Basemap: <link href="https://www.openstreetmap.org/copyright" color="#067e79">OpenStreetMap contributors</link>. Review provider terms before redistribution or public hosting.',y,10,leading=14)
c.showPage()

# 9: Maintenance
y=header(9,'Operate / maintain','Run it. Keep it current.','Local React/Vite frontend, Python HTTP API and SQLite database.')
y=para('Requirements: Node.js 20.19+ (or 22.12+) and Python 3.9+. NumPy is required for offline model fitting and the full tests, not for serving the app or asking-price comparisons.',y)
y=code(['npm install','python3 -m pip install -r requirements-models.txt','npm run import','npm run model','npm run build','npm start'],y)
y=para('Open http://127.0.0.1:8000. Set HDB_PYTHON if needed, using the same interpreter for NumPy installation. Stop with Ctrl+C. Use npm start -- --port 8001 for another port.',y,10)
y=section('Refresh and verify',y)
y=para('Stop the server before replacing data. The specifically named newer 2017-onward snapshot supersedes the older one; avoid other overlapping resale files. Import validates rows and atomically replaces SQLite only on success.',y,10)
y=code(['npm run import','npm run model','npm test','npm run build','npm start'],y)
y=para('Restart clears API caches. Model artifacts are tied to the database and must be regenerated after import. For frontend development, keep the backend running and use npm run dev in another terminal.',y,10)
y=para('<b>Further reference:</b> docs/wiki/Home.md; Asking-Price.md; Price-Equations.md; Architecture-and-API.md; Maintenance.md. The README embeds these current screenshots. Rebuild this guide with python3 scripts/build_guide.py (reportlab and Pillow).',y,9,leading=13)
c.showPage();c.save()
print(OUT)
