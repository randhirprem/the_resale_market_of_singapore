import {useEffect,useState} from 'react';
import {Search,ChevronLeft,ChevronRight,ArrowDown,Download,Database} from 'lucide-react';
import {getJSON,queryString,money,number,titleCase,monthLabel} from './utils';
import {Empty,PanelHeading} from './Charts';
export default function Transactions({filters}){
  const [search,setSearch]=useState(''),[page,setPage]=useState(1),[result,setResult]=useState(null),[loading,setLoading]=useState(true),[error,setError]=useState('');
  useEffect(()=>{
    const controller=new AbortController();setLoading(true);setError('');
    const timer=setTimeout(()=>getJSON('/api/transactions?'+queryString({...filters,search,page}),controller.signal).then(setResult).catch(e=>{if(e.name!=='AbortError')setError(e.message);}).finally(()=>{if(!controller.signal.aborted)setLoading(false);}),180);
    return()=>{clearTimeout(timer);controller.abort();};
  },[filters,search,page]);
  const exportPage=()=>{
    if(!result?.rows.length)return;
    const keys=['month','town','flat_type','block','street_name','storey_range','floor_area_sqm','flat_model','lease_commence_date','remaining_lease','resale_price','price_per_sqm','source'];
    const escape=v=>'"'+String(v??'').replaceAll('"','""')+'"';
    const csv=[keys.join(','),...result.rows.map(r=>keys.map(k=>escape(r[k])).join(','))].join('\r\n');
    const link=document.createElement('a');const url=URL.createObjectURL(new Blob([csv],{type:'text/csv;charset=utf-8;'}));link.href=url;link.download=`hdb-transactions-page-${page}.csv`;link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
  };
  const pages=result?Math.max(1,Math.ceil(result.total/result.page_size)):1;
  return <section className="panel transactions-panel" id="transactions"><PanelHeading eyebrow="05 / TRANSACTION EXPLORER" title="Every sale has a story"><button className="outline-button" disabled={loading||!result?.rows.length} onClick={exportPage}><Download size={14}/>Export page</button></PanelHeading><div className="table-toolbar"><label className="search-input"><Search size={16}/><input aria-label="Search block or street" placeholder="Search block or street name…" value={search} onChange={e=>{setSearch(e.target.value);setPage(1);}}/></label><span className="table-count" role="status">{loading?'QUERYING DATA…':result?number(result.total)+' TRANSACTIONS':''}</span></div>{error?<div className="error-state" role="alert">{error}</div>:<div className={'table-scroll '+(loading?'is-loading':'')} aria-busy={loading}><table><thead><tr><th>Month <ArrowDown size={11}/></th><th>Town / Address</th><th>Flat type</th><th>Storey</th><th>Area</th><th>Lease from</th><th>Remaining lease</th><th>Resale price</th><th>Price / m²</th></tr></thead><tbody>{result?.rows.map(row=><tr key={row.id}><td>{monthLabel(row.month)}</td><td><strong>{titleCase(row.town)}</strong><span>{row.block} {titleCase(row.street_name)}</span></td><td><span className="flat-badge">{titleCase(row.flat_type)}</span><small>{titleCase(row.flat_model)}</small></td><td>{row.storey_range}</td><td>{number(row.floor_area_sqm,1)} <span className="muted">m²</span></td><td>{row.lease_commence_date}</td><td>{row.remaining_lease==null?'Not supplied':number(row.remaining_lease,1)+' yrs'}</td><td className="table-price">{money(row.resale_price)}</td><td>{money(row.price_per_sqm)}</td></tr>)}</tbody></table>{!loading&&!result?.rows.length&&<Empty text="No matching transactions."/>}{loading&&!result&&<div className="table-loading">Loading transactions…</div>}</div>}<div className="pagination"><span>{result?.total?`${number((page-1)*result.page_size+1)}–${number(Math.min(page*result.page_size,result.total))} of ${number(result.total)}`:'0 results'}<span className="pagination-note"> · Latest first</span></span><div><button aria-label="Previous page" disabled={page===1||loading} onClick={()=>setPage(p=>p-1)}><ChevronLeft size={16}/></button><span>Page {page} / {number(pages)}</span><button aria-label="Next page" disabled={page>=pages||loading} onClick={()=>setPage(p=>p+1)}><ChevronRight size={16}/></button></div></div></section>;
}
