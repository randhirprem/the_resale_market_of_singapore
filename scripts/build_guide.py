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
    summary=dashboard(con,{'start':'2024-01','end':'2024-12'})['summary']


def para(text,y,size=10.5,color=INK,width=CW,leading=15):
    style=ParagraphStyle('body',fontName='Helvetica',fontSize=size,leading=leading,textColor=color)
    p=Paragraph(text,style);_,height=p.wrap(width,H)
    p.drawOn(c,M,y-height)
    return y-height-10


def header(num,kicker,title,subtitle=None):
    c.setFillColor(white);c.rect(0,0,W,H,fill=1,stroke=0)
    c.setFillColor(CYAN);c.rect(M,H-39,27,3,fill=1,stroke=0)
    c.setFont('Helvetica-Bold',8);c.drawString(M+37,H-39,'HDB / ATLAS')
    c.setFillColor(MUTED);c.setFont('Helvetica',8);c.drawRightString(W-M,H-39,kicker.upper())
    c.setStrokeColor(HexColor('#dce3eb'));c.line(M,43,W-M,43)
    c.setFillColor(MUTED);c.setFont('Helvetica',8);c.drawString(M,28,'HDB Atlas  |  Historical resale intelligence')
    c.drawRightString(W-M,28,f'{num:02d} / 06')
    y=H-88
    y=para(title,y,25,INK,leading=30)
    if subtitle:y=para(subtitle,y,10.5,MUTED)
    return y-9


def section(title,y):
    return para(title,y,13,CYAN,leading=18)


def shot(name,y,caption,caption_color=MUTED):
    path=ROOT/'docs/screenshots'/name
    with Image.open(path) as im: iw,ih=im.size
    height=CW*ih/iw
    c.drawImage(str(path),M,y-height,width=CW,height=height,preserveAspectRatio=True)
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
c.setFillColor(DARK);c.rect(0,0,W,H,fill=1,stroke=0)
c.setFillColor(HexColor('#3ee7d4'));c.rect(M,H-55,28,3,fill=1,stroke=0)
c.setFont('Courier',10);c.drawString(M,H-79,'SINGAPORE / RESALE INTELLIGENCE')
c.setFillColor(white);c.setFont('Helvetica-Bold',40);c.drawString(M,H-139,'HDB / ATLAS')
c.setFillColor(HexColor('#3ee7d4'));c.setFont('Helvetica',25);c.drawString(M,H-177,'The city. Decoded.')
y=para('USER &amp; PROJECT GUIDE',H-210,10,HexColor('#f099cd'))
y=para('A map-first view of Singapore resale prices, with linked trends, town comparisons and the transactions behind the numbers.',y,12,HexColor('#c1ccdd'),leading=18)-15
y=shot('overview.jpg',y,'Default dashboard: January-December 2024, all towns and flat types.',HexColor('#a6b6ca'))
y=para(f'<b>{meta["count"]:,} transactions</b>  /  Five local datasets<br/>January 1990 - February 2025',y-2,13,HexColor('#d6e6ef'),leading=20)
y=para('Explore the dashboard, understand the calculations, and run or maintain the local app. The accompanying Markdown wiki contains the detailed API reference.',y-6,10.5,HexColor('#a6b6ca'),leading=16)
c.setFillColor(HexColor('#889bb2'));c.setFont('Helvetica',8);c.drawString(M,30,f'Prepared {date.today().isoformat()}  |  Documentation snapshot');c.drawRightString(W-M,30,'01 / 06');c.showPage()

# 2: Map
y=header(2,'Explore / geography','One island. Many markets.','Use location to compare historical transactions, then inspect the homes behind each aggregate.')
y=shot('map.jpg',y,'Town-level medians for January-December 2024. Map attribution is retained in the screenshot.')
y=section('Read the map',y)
y=bullets(['Colour represents the selected median price measure. Toggle Resale price or Price / m²; the legend rescales to the current comparison.','Marker size represents transaction count. Hover for the median and sample size, or click a marker to select a town.','Town selection updates the summary, trend, flat profile and table. The map and ranking retain island-wide comparisons for the chosen dates and flat type.','Use + / - to zoom, Reset map view to reframe, and Expand map for a larger view. Escape closes the expanded map.'],y)
y=section('Location has limits',y)
y=para('Markers are representative planning-area centroids, not individual HDB blocks. URA planning areas provide context rather than exact HDB town boundaries. Kallang represents Kallang/Whampoa; Downtown Core represents Central Area.',y)
c.showPage()

# 3: Analytics
y=header(3,'Explore / analysis','Follow the signal.','Choose a comparable set of homes before interpreting differences in price.')
y=shot('analytics.jpg',y,'Monthly trend, flat-type mix and town comparisons in the default 2024 view.')
y=section('Filter, then compare',y)
y=bullets(['From and To are inclusive month filters. Flat type and Town refine the selected transactions. Reset returns to January-December 2024.','Trend modes show monthly median price, median price per m², or volume. Zero-sale months have zero volume and no price median.','Flat profile shows transaction shares. Compare prices switches to median price by flat type. Town rankings use the same price measure as the map.'],y)
y=section('A reproducible comparison',y)
y=para('For 2024, 4 ROOM flats in BEDOK have <b>452 sales</b> and a <b>$540,000</b> median price. Selecting TAMPINES gives <b>867 sales</b> and a <b>$625,000</b> median. These observations are not current asking prices or valuation estimates.',y)
c.showPage()

# 4: Transactions
y=header(4,'Explore / records','Every sale has a story.','Trace aggregate patterns back to the source records.')
y=shot('transactions.jpg',y,'The transaction explorer shows 12 records per page, with address search and CSV export.')
y=section('Search and export',y)
y=bullets(['Search block or street names. Search affects only the table; shared date, town and flat-type filters apply across the dashboard.','Rows are ordered by month descending, then import ID. The data does not specify the order of sale within each month.','Export page downloads the current page, not the entire matching dataset. The 13-column CSV includes the source filename.','A new search resets pagination. Shared-filter changes reset the table. Copy the URL to preserve date, town and flat-type filters; search and page are not included.'],y)
y=section('Understand the fields',y)
y=para('The table includes month, town and address, flat type/model, storey range, floor area, lease commencement year, remaining lease, price and price per m². Remaining lease is shown only when supplied; older rows are not filled with estimates.',y)
c.showPage()

# 5: Data
y=header(5,'Reference / data','Know your data.','Coverage, exact calculations and the qualifications needed for sound comparisons.')
y=table(['Period','Rows','Date basis'],[
('1990-1999','287,196','Approval'),('2000-Feb 2012','369,651','Approval'),('Mar 2012-Dec 2014','52,203','Registration'),('2015-2016','37,153','Registration'),('2017-Feb 2025','201,167','Registration'),('TOTAL','947,370','Five local CSVs')],[220,110,CW-330],y)
y=section('Exact medians, individual transactions',y)
y=para('The median price is calculated over matching sale prices. Price per m² is computed for <i>each transaction</i> before taking its median. Median area is calculated independently. Subgroup medians are never averaged. Duplicate-looking source rows are preserved.',y)
y=table(['2024 baseline','Value'],[('Transaction count',f'{summary["count"]:,}'),('Median resale price',f'SGD {summary["price"]:,.0f}'),('Median price per m²',f'SGD {summary["psm"]:,.2f}'),('Median floor area',f'{summary["area"]:g} m²')],[300,CW-300],y)
y=para('<b>Interpretation:</b> prices are nominal SGD, not inflation-adjusted. Changes can reflect the mix of homes sold. The date basis changes in March 2012. February 2025 may be incomplete. There is no live refresh or predictive valuation model.',y,10,leading=14)
y=para('<b>Sources:</b> five root CSVs (exact filenames in the wiki); <link href="https://data.gov.sg/datasets/d_4765db0e87b9c86336792efe8a1f7a66/view" color="#067e79">URA Master Plan 2019 planning areas</link> under the Singapore Open Data Licence; basemap by <link href="https://www.openstreetmap.org/copyright" color="#067e79">OpenStreetMap contributors</link>.',y,9,leading=13)
c.showPage()

# 6: Maintainers
y=header(6,'Operate / maintain','Run it. Keep it current.','The application runs locally with React, Leaflet, Recharts, Python and SQLite.')
y=section('Start the app',y)
y=para('Requirements: Node.js 20.19+ (or 22.12+) and Python 3.9+. Run these commands from the project root:',y)
y=code(['npm install','npm run build','npm start'],y)
y=para('Open <link href="http://127.0.0.1:8000" color="#067e79">http://127.0.0.1:8000</link>. The first start imports root CSVs if the database is absent. Stop with Ctrl+C. Set HDB_PYTHON if interpreter discovery fails. Use npm start -- --port 8001 for another port.',y)
y=section('Refresh data safely',y)
y=para('Stop the server. Replace source CSVs with non-overlapping files, then import and restart. The importer preserves every row, so overlapping versions would double-count. Invalid rows abort the import and leave the old database intact.',y)
y=code(['npm run import','npm test','npm start'],y)
y=para('Restart after import to clear cached API responses. Rebuild the frontend after UI changes. For development, run npm run dev in a second terminal while the backend runs on port 8000.',y)
y=section('Architecture and further reference',y)
y=para('CSV files feed an indexed SQLite database. A read-only Python API serves metadata, dashboard aggregates and paginated transactions. React consumes that API; local URA geometry supplies map context. Online tiles and optional fonts require internet.',y)
y=para('<b>Wiki:</b> docs/wiki/Home.md<br/><b>API reference:</b> docs/wiki/Architecture-and-API.md<br/><b>Maintenance:</b> docs/wiki/Maintenance.md<br/><b>Screenshots:</b> docs/screenshots/<br/><b>Rebuild this guide:</b> python3 scripts/build_guide.py (reportlab and Pillow required).',y,10,leading=15)
y=para('The standard-library server is for local use. Hosting, authentication and block-level geocoding are outside this version.',y,9,MUTED,leading=13)
c.showPage();c.save()
print(OUT)
