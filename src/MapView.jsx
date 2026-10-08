import {useEffect,useRef,useState} from 'react';
import L from 'leaflet';
import ContextLayers from './ContextLayers';
import {Crosshair, MapPin, X} from 'lucide-react';
import {money,number,titleCase} from './utils';

// Area-weighted centroid of each polygon's outer ring, derived from URA geometry.
function center(geometry) {
  const polygons=geometry.type==='MultiPolygon'?geometry.coordinates:[geometry.coordinates];
  let total=0,x=0,y=0;
  for(const [ring] of polygons){
    let area=0,cx=0,cy=0;
    for(let i=0;i<ring.length-1;i++){
      const [ax,ay]=ring[i], [bx,by]=ring[i+1],cross=ax*by-bx*ay;
      area+=cross;cx+=(ax+bx)*cross;cy+=(ay+by)*cross;
    }
    if(Math.abs(area)>1e-12){const weight=Math.abs(area);x+=cx/(3*area)*weight;y+=cy/(3*area)*weight;total+=weight;}
  }
  return total?[y/total,x/total]:[1.35,103.82];
}
const initialBounds=[[1.27,103.67],[1.47,104.01]];
function priceColor(price, min, max){const t=max===min?0.5:(price-min)/(max-min);return t>.72?'#f05eb9':t>.44?'#a88aff':t>.2?'#6da9ff':'#3ee7d4';}

export default function MapView({towns,selected,onSelect,metric,contextLayers=[],catalogError,onRetryCatalog}){
  const element=useRef(null), map=useRef(null), layers=useRef(null), selection=useRef(onSelect);
  const [geo,setGeo]=useState(null),[error,setError]=useState(''),[tilesFailed,setTilesFailed]=useState(false),[mapReady,setMapReady]=useState(false);
  selection.current=onSelect;
  useEffect(()=>{
    const controller=new AbortController();
    fetch('/data/planning-areas.geojson',{signal:controller.signal}).then(r=>{if(!r.ok)throw Error();return r.json();}).then(setGeo).catch(e=>{if(e.name!=='AbortError')setError('Map boundaries could not load. Town comparisons remain available below.');});
    return ()=>controller.abort();
  },[]);
  useEffect(()=>{
    const instance=L.map(element.current,{zoomControl:false,attributionControl:true,scrollWheelZoom:false,zoomSnap:.25,minZoom:10,maxZoom:16});
    instance.fitBounds(initialBounds,{padding:[10,10]});map.current=instance;setMapReady(true);
    L.control.zoom({position:'bottomright'}).addTo(instance);
    instance.createPane('context');instance.getPane('context').style.zIndex='450';
    const tiles=L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png',{
      attribution:'&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> · <a href="https://data.gov.sg/datasets/d_4765db0e87b9c86336792efe8a1f7a66/view">URA 2019</a>',maxZoom:19});
    tiles.on('tileerror',()=>setTilesFailed(true));tiles.addTo(instance);
    layers.current=L.layerGroup().addTo(instance);
    const resize=new ResizeObserver(()=>instance.invalidateSize());resize.observe(element.current);
    return ()=>{resize.disconnect();instance.remove();map.current=null;};
  },[]);
  useEffect(()=>{
    if(!geo||!map.current)return;
    const group=layers.current;group.clearLayers();
    const field=metric==='psm'?'psm':'price', values=towns.map(t=>t[field]);
    const min=Math.min(...values),max=Math.max(...values),maxCount=Math.max(...towns.map(t=>t.count),1);
    const indexed=Object.fromEntries(towns.map(t=>[t.town,t]));
    const townName=f=>f.properties.CA_IND==='Y'?'CENTRAL AREA':f.properties.PLN_AREA_N==='KALLANG'?'KALLANG/WHAMPOA':f.properties.PLN_AREA_N;
    L.geoJSON(geo,{style:f=>{
      const name=townName(f),row=indexed[name],active=name===selected;
      return {color:active?'#e9fffa':row?priceColor(row[field],min,max):'#29414b',weight:active?2:0.8,fillColor:row?priceColor(row[field],min,max):'#12212a',fillOpacity:active?.3:row?.09:.2,opacity:active?1:.5};
    },onEachFeature:(feature,layer)=>{
      const name=townName(feature);
      if(indexed[name])layer.on('click',()=>selection.current(name));
    }}).addTo(group);
    const visited=new Set();
    for(const feature of geo.features){
      const name=townName(feature),row=indexed[name];
      if(!row||visited.has(name))continue;
      // Downtown Core represents the historical HDB Central Area aggregate.
      if(name==='CENTRAL AREA'&&feature.properties.PLN_AREA_N!=='DOWNTOWN CORE')continue;
      visited.add(name);
      const pos=center(feature.geometry),color=priceColor(row[field],min,max),active=name===selected;
      L.circleMarker(pos,{radius:9+Math.sqrt(row.count/maxCount)*14,color,weight:1,fillColor:color,fillOpacity:active?.32:.14,opacity:.85}).addTo(group).on('click',()=>selection.current(name));
      const marker=L.marker(pos,{keyboard:true,title:titleCase(name),icon:L.divIcon({className:'town-marker',html:`<span style="--marker-color:${color}" class="marker-core ${active?'selected':''}"></span>`,iconSize:[28,28],iconAnchor:[14,14]})}).addTo(group);
      marker.on('click',()=>selection.current(name));
      const tip=document.createElement('div');
      const strong=document.createElement('strong');strong.textContent=titleCase(name);tip.append(strong);
      const detail=document.createElement('div');detail.textContent=`${money(row[field])}${field==='psm'?' / m²':''} · ${number(row.count)} sales`;tip.append(detail);
      marker.bindTooltip(tip,{direction:'top',offset:[0,-10],className:'map-tooltip'});
      if(row.count>=maxCount*.38||active){
        const label=L.marker(pos,{interactive:false,keyboard:false,icon:L.divIcon({className:'town-label',html:titleCase(name),iconSize:[120,20],iconAnchor:[60,-18]})});label.addTo(group);
      }
    }
  },[geo,towns,selected,metric]);
  const field=metric==='psm'?'psm':'price',values=towns.map(t=>t[field]);
  return <>{mapReady&&<ContextLayers map={map} layers={contextLayers} error={catalogError} onRetry={onRetryCatalog}/>}<div className="map-wrap">
    <div ref={element} className="map-canvas" aria-label="Interactive Singapore map with town median prices"/>
    <div className="map-stamp"><span className="live-dot"/> SINGAPORE <span className="map-coordinates">1.3521° N / 103.8198° E</span></div>
    <button className="map-reset icon-button" title="Reset map view" aria-label="Reset map view" onClick={()=>map.current?.fitBounds(initialBounds)}><Crosshair size={18}/></button>
    {selected&&<button className="map-selection" onClick={()=>onSelect('')}><MapPin size={13}/>{titleCase(selected)}<X size={14}/></button>}
    <div className="map-legend"><span>MEDIAN {metric==='psm'?'PRICE / M²':'RESALE PRICE'}</span><div className="legend-gradient"/><div><b>{values.length?money(Math.min(...values)):'—'}</b><b>{values.length?money(Math.max(...values)):'—'}</b></div><small>Marker size = transaction volume</small></div>
    <div className="map-instruction">{error|| (tilesFailed?'Offline basemap · local boundaries shown':'Select a town to explore · use + / − to zoom')}</div>
  </div></>;
}
