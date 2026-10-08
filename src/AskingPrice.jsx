import {useEffect,useRef,useState} from 'react';
import {PanelHeading} from './Charts';
import {getJSON,money,number,monthLabel,titleCase} from './utils';

const assessments={
  above_range:{label:'Asking price looks high',outcome:'Below asking is better supported',description:'Your asking price exceeds the upper quartile of matching recorded sales. A price reduction is better supported by this comparison unless the home has features that justify a premium.'},
  within_range:{label:'Asking price is within the comparison range',outcome:'A sale at asking is supported by comparables',description:'Your asking price sits within the middle half of matching recorded sales. At asking is plausible; negotiation below asking remains possible.'},
  below_range:{label:'Asking price is below the comparison range',outcome:'A sale at asking is supported by comparables',description:'Your asking price is below the lower quartile of matching recorded sales. Check whether size, condition or other differences explain the gap. This does not establish a bidding war or a sale above asking.'}
};
export default function AskingPrice({meta}){
  const [form,setForm]=useState({town:'',asking:'',flat_type:'4 ROOM',lease:''});
  const [result,setResult]=useState(null),[error,setError]=useState(''),[busy,setBusy]=useState(false);
  const request=useRef(null);
  useEffect(()=>()=>request.current?.abort(),[]);
  function change(key,value){request.current?.abort();setBusy(false);setResult(null);setError('');setForm(f=>({...f,[key]:value}));}
  async function submit(event){
    event.preventDefault();request.current?.abort();const controller=new AbortController();request.current=controller;
    setBusy(true);setError('');setResult(null);
    try {setResult(await getJSON('/api/asking?'+new URLSearchParams(form),controller.signal));}
    catch(e){if(e.name!=='AbortError')setError(e.message);}
    finally {if(!controller.signal.aborted)setBusy(false);}
  }
  const assessment=result&&assessments[result.status];
  return <section className="panel asking-panel" id="asking">
    <PanelHeading eyebrow="ASKING PRICE / COMPARABLE SALES" title="Is the asking price supported?"/>
    <div className="asking-body"><p>Enter a flat’s details to compare the asking price with recent completed sales. This form uses its own inputs, independently of the dashboard filters.</p>
      <form className="asking-form" onSubmit={submit}>
        <label htmlFor="asking-estate">Estate<select id="asking-estate" required value={form.town} onChange={e=>change('town',e.target.value)}><option value="">Choose an estate</option>{meta?.towns.map(t=><option key={t} value={t}>{titleCase(t)}</option>)}</select></label>
        <label htmlFor="asking-price">Asking price (SGD)<input id="asking-price" type="number" inputMode="decimal" min="1" step="0.01" required placeholder="e.g. 650000" value={form.asking} onChange={e=>change('asking',e.target.value)}/></label>
        <label htmlFor="asking-type">Housing type<select id="asking-type" required value={form.flat_type} onChange={e=>change('flat_type',e.target.value)}>{(meta?.flat_types||['4 ROOM']).map(t=><option key={t} value={t}>{titleCase(t)}</option>)}</select></label>
        <label htmlFor="asking-lease">Remaining lease (years)<input id="asking-lease" type="number" inputMode="decimal" min="0.1" max="99" step="0.1" required placeholder="e.g. 70.5" value={form.lease} onChange={e=>change('lease',e.target.value)}/></label>
        <button className="asking-submit" disabled={busy||!meta} type="submit">{busy?'Comparing sales…':'Assess asking price'}</button>
      </form>
      {error&&<p className="error-state" role="alert">{error}</p>}
      <div aria-live="polite" aria-busy={busy}>
        {busy&&<p>Finding comparable completed sales…</p>}
        {result&&<div className="asking-result">
          <p className="eyebrow">{titleCase(result.town)} · {titleCase(result.flat_type)} · {number(result.lease,1)} years remaining</p>
          {assessment?<>
            <h3>{assessment.label}</h3>
            <div className="asking-cards">
              <article><span>PRICE-BASED OUTCOME ASSESSMENT</span><strong>{assessment.outcome}</strong><p>{assessment.description}</p></article>
              <article><span>INDICATIVE ACCEPTABLE PRICE RANGE</span><strong>{money(result.range[0])} – {money(result.range[1])}</strong><p>Middle 50% of comparable completed sale prices. A historical benchmark, not a valuation or a predicted sale-price interval.</p></article>
              <article><span>ASKING VERSUS COMPARABLE MEDIAN</span><strong>{money(result.asking)} versus {money(result.median)}</strong><p>{number(Math.abs(result.gap_pct),1)}% {result.gap_pct>=0?'above':'below'} the comparable median. Sample floor areas span {number(result.area_range[0])}–{number(result.area_range[1])} m².</p></article>
            </div>
            <p className="model-warning">Sale likelihood is not estimated: these records contain completed sales, without the unsold listings needed to calculate a probability. “At asking supported” describes price evidence, not a promise that the home will sell.</p>
          </>:<><h3>Not enough comparable sales for an assessment</h3><p>Found {number(result.count)} sales across {number(result.blocks)} blocks. At least 20 sales across 3 blocks are required. No price range or sale-outcome assessment is issued.</p></>}
          <p>{number(result.count)} matching sales across {number(result.blocks)} blocks · {monthLabel(result.start)}–{monthLabel(result.end)} · recorded remaining leases {number(result.lease_band[0],1)}–{number(result.lease_band[1],1)} years.</p>
          <details><summary>Comparison method and supporting sales</summary><p>Same estate and flat type; remaining lease within five years; previous 12 months before the latest source month. All floor areas and storeys are included. The range uses the 25th and 75th percentiles, without adjusting for size, exact location, renovations, views or accessibility. Those differences can justify prices outside the range. This comparison does not use the estate regression equation.</p>
            {result.examples.length>0&&<div className="reference-table" role="region" aria-label="Recent comparable sales" tabIndex={0}><table><thead><tr><th>Month</th><th>Block / street</th><th>Area</th><th>Storeys</th><th>Lease</th><th>Sale price</th></tr></thead><tbody>{result.examples.map((r,i)=><tr key={i}><td>{monthLabel(r.month)}</td><td>{r.block} {titleCase(r.street_name)}</td><td>{number(r.floor_area_sqm)} m²</td><td>{r.storey_range}</td><td>{number(r.remaining_lease,1)} years</td><td>{money(r.resale_price)}</td></tr>)}</tbody></table><p>Up to 10 of the most recent matching records. These are comparison sales, not identified outcomes for your listing.</p></div>}
          </details>
        </div>}
      </div>
    </div>
  </section>;
}
