import {useEffect, useState} from 'react';
import {ChevronLeft, ChevronRight, Search, Database} from 'lucide-react';
import {PanelHeading} from './Charts';
import {getJSON, number} from './utils';

const label = key => ({blk_no:'Block', max_floor_lvl:'Maximum floor', total_dwelling_units:'Dwelling units',
  balanced_score:'Balanced score / 100', median_recorded_minutes:'Median recorded time (min)',
  origins_within_30_minutes:'Station origins within 30 min', subject_listings:'Unique subject listings', cca_choices:'CCA choices',
  dgp_code:'Planning area', mainlevel_code:'School level', bldg_contract_town:'HDB town code',
  mrt_desc:'MRT access', ccas:'CCAs', moe_programmes:'MOE programmes', url_address:'Website',
  TimeTaken_Mins:'Travel time (minutes)', DistanceTravelled_KM:'Travel distance (km)'}[key] || key.replaceAll('_',' '));
const useful = value => value && !['na','null','nil'].includes(String(value).toLowerCase());
const previewFields = {
  schools:['address','mainlevel_code','dgp_code','mrt_desc'],
  buildings:['year_completed','max_floor_lvl','total_dwelling_units','bldg_contract_town'],
};

function RecordCard({row, dataset}) {
  const title=dataset==='schools'?row.school_name:`Block ${row.blk_no} · ${row.street}`;
  return <article className="reference-card">
    <h3>{title}</h3>
    <dl>{previewFields[dataset].map(key=><div key={key}><dt>{label(key)}</dt><dd>{row[key] || '—'}</dd></div>)}</dl>
    <details><summary>{dataset==='schools'?'Subjects, CCAs & school details':'Building details & flat mix'}</summary>
      <dl className="reference-details">{Object.entries(row).filter(([,value])=>useful(value)).map(([key,value])=><div key={key}><dt>{label(key)}</dt><dd>{value}</dd></div>)}</dl>
    </details>
  </article>;
}

export default function ReferenceExplorer({catalog, catalogError, onRetry}) {
  const [dataset,setDataset]=useState('school-rankings'),[search,setSearch]=useState(''),[page,setPage]=useState(1);
  const [data,setData]=useState(null),[error,setError]=useState(''),[loading,setLoading]=useState(true),[retry,setRetry]=useState(0);
  const available=catalog?.datasets || [];
  const active=available.find(item=>item.id===dataset);
  useEffect(()=>{
    if(available.length && !active) setDataset(available[0].id);
  },[catalog,dataset]);
  useEffect(()=>{
    if(!active){setLoading(false);return;}
    const controller=new AbortController();setLoading(true);setError('');setData(null);
    const timer=setTimeout(()=>getJSON('/api/context/records?'+new URLSearchParams({dataset,search,page,page_size:12}),controller.signal)
      .then(setData).catch(e=>{if(e.name!=='AbortError')setError(e.message);})
      .finally(()=>{if(!controller.signal.aborted)setLoading(false);}),180);
    return()=>{clearTimeout(timer);controller.abort();};
  },[dataset,search,page,retry,active]);
  const cards=dataset==='schools'||dataset==='buildings';
  return <section className="panel reference-panel" id="neighbourhood">
    <PanelHeading eyebrow="06 / NEIGHBOURHOOD CONTEXT" title="Explore beyond the sale."><Database size={20}/></PanelHeading>
    <p className="reference-intro">Explore schools, HDB buildings, markets and transport. These reference snapshots have their own coverage and are independent of the resale filters above.</p>
    <details className="accessibility-guide"><summary>How schools and accessibility can affect daily life and resale prices</summary>
      <p>Convenience depends on your destinations and the actual route. A nearby station exit, school or park is a starting point; it does not measure a sheltered, step-free or safe walk.</p>
      <div className="reference-table"><table><thead><tr><th>Factor</th><th>Everyday-life considerations</th><th>Resale-price interpretation</th></tr></thead><tbody>
        <tr><td>School fit</td><td>Subjects, CCAs, eligibility and a manageable school run matter more than a single score.</td><td>School proximity can influence demand. The balanced score here does not measure popularity, admission chances or a price premium.</td></tr>
        <tr><td>MRT / LRT access</td><td>Consider the whole trip: walk, transfers, waiting and the destination. Nearby elevated tracks can add noise.</td><td>Station convenience and track noise can pull prices in opposite directions. Exit counts are not distinct station counts.</td></tr>
        <tr><td>Hawkers and community facilities</td><td>Nearby food, activities and services can make daily errands easier; crowds, traffic and opening hours also matter.</td><td>These are possible demand factors. This dataset does not isolate their contribution to sale prices.</td></tr>
        <tr><td>Parks, tracks and cycling paths</td><td>Connected routes and usable entrances matter more than the number of mapped segments. Route comfort and accessibility are not measured here.</td><td>Open-space access may influence preferences; fragmented paths and large parks cannot be compared by feature count alone.</td></tr>
        <tr><td>Car parks and sensitive land uses</td><td>Car park outlines do not reveal available spaces. Preferences around cemeteries and after-death facilities differ between households.</td><td>No universal positive or negative adjustment is supported by these files.</td></tr>
      </tbody></table></div>
      <p><strong>What is still missing for a local price-impact estimate:</strong> verified block and school coordinates, walking routes, facility dates, and comparable-flat controls for sale month, floor area, lease, storey and location. Town medians alone cannot separate these effects. More amenities can coincide with expensive locations without causing the entire price difference.</p>
      <p>Research context: <a href="https://ireus.nus.edu.sg/mrt-and-property-value/" target="_blank" rel="noreferrer">NUS on station access versus track noise</a> · <a href="https://news.nus.edu.sg/how-school-proximity-affects-house-prices/" target="_blank" rel="noreferrer">NUS on school proximity</a>. These studies support possible mechanisms, not a percentage adjustment for the current data.</p>
    </details>
    {catalogError?<div className="error-state" role="alert">{catalogError}<button className="text-button" onClick={onRetry}>Retry sources</button></div>:<>
      <div className="reference-controls">
        <label>Reference dataset<select value={dataset} onChange={e=>{setDataset(e.target.value);setSearch('');setPage(1);}}>{available.map(item=><option value={item.id} key={item.id}>{item.label}</option>)}</select></label>
        <label>Search all fields<div className="reference-search"><Search size={17}/><input type="search" value={search} placeholder={dataset==='schools'?'School, area, subject or CCA…':dataset==='buildings'?'Block, street or town code…':'Name, station, year or keyword…'} onChange={e=>{setSearch(e.target.value);setPage(1);}}/></div></label>
      </div>
      <div className="reference-status" role="status">{loading?'Loading reference records…':data?`${number(data.total)} matches · ${number(data.source_count)} source records`:available.length?'':'No reference datasets found.'}</div>
      {dataset==='school-rankings'&&data&&<div className="ranking-method"><p><strong>50% transport access · 25% subjects · 25% CCAs.</strong> Ranked across {data.source_count} comparable schools, with {data.origins} station origins per school. These are source-recorded times, not walking times.</p><details><summary>How to read this ranking</summary><p>{data.methodology}</p>{data.excluded.length>0&&<><p>Excluded rather than assigned a misleading score:</p><ul>{data.excluded.map(item=><li key={item.school}>{item.school}: {item.reason}</li>)}</ul></>}</details></div>}
      {dataset==='school-travel'&&<p className="reference-note">Travel times and distances are supplied reference values, not live routing or distances from a resale flat.</p>}
      {['cars','rail','courses'].includes(dataset)&&<p className="reference-note">Singapore-wide historical statistics; years shown belong to this source and do not follow the resale date filter.</p>}
      {error&&<div className="error-state" role="alert">{error}<button className="text-button" onClick={()=>setRetry(r=>r+1)}>Retry</button></div>}
      <div aria-busy={loading} className="reference-results">
        {loading?<div className="table-loading">Loading…</div>:data?.rows.length?cards?<div className="reference-grid">{data.rows.map((row,i)=><RecordCard key={`${dataset}-${page}-${i}`} row={row} dataset={dataset}/>)}</div>:<div className="reference-table" tabIndex={0} role="region" aria-label="Reference data table, scroll horizontally for more columns"><table><thead><tr>{data.columns.map(key=><th key={key} scope="col">{label(key)}</th>)}</tr></thead><tbody>{data.rows.map((row,i)=><tr key={i}>{data.columns.map(key=><td key={key}>{row[key] ?? '—'}</td>)}</tr>)}</tbody></table></div>:!error&&<div className="empty-state">No matching records. Try another search.</div>}
      </div>
      <div className="pagination"><span>{data?`Page ${page} of ${Math.max(1,Math.ceil(data.total/12))}`:'Reference records'}</span><div><button aria-label="Previous reference page" disabled={loading||page===1} onClick={()=>setPage(p=>p-1)}><ChevronLeft size={16}/></button><button aria-label="Next reference page" disabled={loading||!data||page*12>=data.total} onClick={()=>setPage(p=>p+1)}><ChevronRight size={16}/></button></div></div>
      {active&&<p className="reference-source">Source: {active.file}{dataset==='schools'?' · Linked to local subjects, CCAs, MOE and distinctive programme files by school name.':''}</p>}
    </>}
  </section>;
}
