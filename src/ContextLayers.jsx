import {useEffect, useState} from 'react';
import L from 'leaflet';
import {getJSON, number} from './utils';

function popup(feature, title) {
  const box=document.createElement('div');box.className='context-popup';
  const heading=document.createElement('strong');heading.textContent=title;box.append(heading);
  const props=feature.properties || {};
  const keys=Object.keys(props).filter(key=>!['INC_CRC','FMEL_UPD_D','OBJECTID','OBJECTID_1','PHOTOURL'].includes(key));
  for(const key of keys){
    const value=props[key];
    if(value===null||value==='')continue;
    const line=document.createElement('p');
    const name=document.createElement('b');name.textContent=key.replaceAll('_',' ')+': ';
    line.append(name,document.createTextNode(String(value)));box.append(line);
  }
  return box;
}

export default function ContextLayers({map, layers, error, onRetry}) {
  const [selected,setSelected]=useState(''),[viewport,setViewport]=useState(''),[status,setStatus]=useState(''),[retry,setRetry]=useState(0),[failed,setFailed]=useState(false);
  const layer=layers.find(item=>item.id===selected);
  useEffect(()=>{
    const instance=map.current;
    if(!instance)return;
    const update=()=>{const b=instance.getBounds();setViewport([Math.max(-180,b.getWest()),Math.max(-90,b.getSouth()),Math.min(180,b.getEast()),Math.min(90,b.getNorth())].join(','));};
    update();instance.on('moveend',update);
    return()=>instance.off('moveend',update);
  },[map]);
  useEffect(()=>{
    const instance=map.current;
    if(!instance||!layer||!viewport){setStatus('');return;}
    const controller=new AbortController();
    const group=L.layerGroup().addTo(instance);
    setStatus('Loading map features…');setFailed(false);
    const timer=setTimeout(()=>getJSON('/api/context/map?'+new URLSearchParams({layer:selected,bbox:viewport}),controller.signal).then(data=>{
      if(controller.signal.aborted)return;
      L.geoJSON(data,{
        pane:'context',
        style:{color:layer.color,weight:2,fillColor:layer.color,fillOpacity:.14},
        pointToLayer:(feature,latlng)=>L.circleMarker(latlng,{pane:'context',radius:5,color:'#10131e',weight:1,fillColor:layer.color,fillOpacity:.95}),
        onEachFeature:(feature,featureLayer)=>featureLayer.bindPopup(()=>popup(feature,layer.label),{maxWidth:320}),
      }).addTo(group);
      setStatus(`${number(data.features.length)} features shown${data.truncated?` of ${number(data.matched)} in view · Zoom in to reveal more`:''}`);
    }).catch(e=>{if(e.name!=='AbortError'){setStatus(e.message);setFailed(true);}}),160);
    return()=>{clearTimeout(timer);controller.abort();group.remove();};
  },[selected,viewport,retry,layer,map]);
  return <div className="context-layer-controls">
    <label htmlFor="context-layer">Map overlay</label>
    <select id="context-layer" value={selected} onChange={e=>setSelected(e.target.value)}><option value="">Resale markets only</option>{layers.map(item=><option key={item.id} value={item.id}>{item.label}</option>)}</select>
    {layer&&<span className="layer-key"><i style={{background:layer.color}}/>{layer.label}</span>}
    <span role="status">{error||status||'Select a layer to explore local amenities and geography.'}</span>
    {(failed||error)&&<button className="text-button" onClick={()=>error?onRetry():setRetry(r=>r+1)}>Retry</button>}
    {layer&&<small className="layer-source">Source: {layer.file} · Independent reference snapshot. School zones are road zones; plan annotations are labels, not park boundaries.</small>}
  </div>;
}
