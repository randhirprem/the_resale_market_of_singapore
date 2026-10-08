import {useEffect,useState} from 'react';
import {Calculator,Info} from 'lucide-react';
import {PanelHeading} from './Charts';
import {getJSON,number,monthLabel,titleCase} from './utils';

const decimal=value=>number(value,3);
const signed=(value,digits=2)=>(value>=0?'+':'−')+number(Math.abs(value),digits);
const effect=(value,step=1)=>(Math.exp(value*step)-1)*100;
const factors=[['log_area','10% more floor area',Math.log(1.1)],['lease','10 more years of lease',1],['floor','10 storeys higher',1],['time','12 months later',1]];
function term(value,name){return `${value>=0?'+':'−'} ${decimal(Math.abs(value))} ${name}`;}
function interval(model,key,step){const bounds=model.intervals[key];return bounds?`${signed(effect(bounds[0],step),1)}% to ${signed(effect(bounds[1],step),1)}%`:'Unavailable';}

function Equation({model,label,national=false,offset=0,validation}){
  const c=model.coefficients;
  return <article className="equation-card">
    <div className="eyebrow">{national?'SINGAPORE BENCHMARK':'ESTATE EQUATION'}</div><h3>{label}</h3>
    <div className="equation-text" aria-label={`${label} log-price equation`}>
      <span>ln(P) ≈ {decimal(c.intercept+offset)}</span>
      <span>{term(c.log_area,'ln(A / 100)')}</span>
      <span>{term(c.lease,'((L − 70) / 10)')}</span>
      <span>{term(c.floor,'((S − 8) / 10)')}</span>
      <span>{term(c.time,'T')} + τflat{national?' + δestate':''}</span>
    </div>
    <p>Convert back to SGD with P ≈ exp(the expression above). This is a fitted geometric price centre, not a guaranteed sale price.</p>
    <div className="equation-stats"><div><strong>{number(model.n)}</strong><span>training sales</span></div><div><strong>{validation?number(validation.mean_ape,1)+'%':'—'}</strong><span>mean test error</span></div></div>
    <details><summary>Flat-type adjustments (τflat)</summary><p>Four-room is the reference (0). These are conditional on floor area; they are not raw differences between flat-type medians.</p><ul>{model.flat_types.map(type=><li key={type}>{titleCase(type)}: {decimal(c['type:'+type]||0)} log points ({signed(effect(c['type:'+type]||0),1)}%)</li>)}</ul></details>
  </article>;
}

function Importance({model}){
  const maximum=Math.max(...model.importance.map(item=>Math.abs(item.error_increase_pp||0)),1);
  return <div className="model-importance">{model.importance.map(item=><div className="importance-row" key={item.group}>
    <span>{item.label}</span><div className="importance-track"><i style={{width:Math.abs(item.error_increase_pp||0)/maximum*100+'%',background:item.error_increase_pp<0?'var(--purple)':'var(--cyan)'}}/></div><b>{item.error_increase_pp==null?'—':signed(item.error_increase_pp,2)+' pp'}</b>
  </div>)}</div>;
}

export default function PriceEquations({selectedTown,onSelectTown}){
  const [report,setReport]=useState(null),[error,setError]=useState(''),[retry,setRetry]=useState(0);
  useEffect(()=>{const controller=new AbortController();setError('');getJSON('/api/models',controller.signal).then(setReport).catch(e=>{if(e.name!=='AbortError')setError(e.message);});return()=>controller.abort();},[retry]);
  const estate=report?.towns.find(row=>row.town===selectedTown);
  const local=estate?.model;
  const national=report?.national;
  const top=(local||national)?.importance.find(item=>item.error_increase_pp>0);
  const localBetter=local?.validation&&local.validation.mean_ape<estate.national_validation.mean_ape;
  return <section className="panel equations-panel" id="equations">
    <PanelHeading eyebrow="07 / PRICE EQUATIONS" title="What holds each market together?"><Calculator size={20}/></PanelHeading>
    <p className="reference-intro">Compare a common Singapore HDB equation with each estate’s own relationships. “Anchors” below mean factors that help predict recorded prices; they do not prove what causes prices. This is a historical comparison, not a valuation or future-price forecast.</p>
    {error?<div className="error-state" role="alert"><Info size={16}/>{error}<button className="text-button" onClick={()=>setRetry(r=>r+1)}>Retry</button></div>:!report?<div className="table-loading" role="status">Loading fitted equations…</div>:<>
      <div className="equation-toolbar"><label>Compare an estate<select value={estate?selectedTown:''} onChange={e=>onSelectTown(e.target.value)}><option value="">Singapore overview</option>{report.towns.map(row=><option key={row.town} value={row.town}>{titleCase(row.town)}</option>)}</select></label><p>Fit: {monthLabel(report.window.start)}–{monthLabel(report.window.train_end)}<br/>Test: {monthLabel(report.window.test_start)}–{monthLabel(report.window.end)}<br/>Fixed model window; date and flat-type filters above do not refit these equations.</p></div>
      <div className="equation-definitions"><strong>Read the equation</strong><span>P = resale price in SGD · A = floor area in m² · L = remaining lease in years · S = midpoint of storey range · T = years since {monthLabel(report.window.reference_month)}.</span><span>τflat = flat-type adjustment. δestate = estate offset in the island model, centred to average zero across training transactions.</span></div>
      {selectedTown&&!estate&&<p className="reference-note">No equation is available for {titleCase(selectedTown)} in this recent model window. The Singapore benchmark is shown below.</p>}
      <div className="equation-grid"><Equation model={national} label="Singapore" national validation={national.validation}/>{estate&&(local?<Equation model={local} label={titleCase(estate.town)} validation={local.validation}/>:<article className="equation-card"><div className="eyebrow">POOLED ESTATE ESTIMATE</div><h3>{titleCase(estate.town)}</h3><p>{estate.reason}</p><div className="equation-text">Use the Singapore equation with δestate = {decimal(estate.national_offset)}.</div><p>This provides an estate equation using shared island slopes. It is not an independently fitted local model.</p><p>{number(estate.training_n)} training sales · {number(estate.test_n)} later sales</p></article>)}</div>
      {estate&&<div className="estate-model-summary"><h3>{titleCase(estate.town)} versus the island</h3><p>The island model’s estate adjustment is <strong>{signed(effect(estate.national_offset),1)}%</strong> relative to its transaction-weighted reference, holding recorded predictors fixed. This offset also includes unmeasured location and housing differences; it cannot be assigned specifically to schools, MRT or parks.</p>{local&&<p>On the same {number(local.validation?.n)} later sales, the local equation has <strong>{number(local.validation?.mean_ape,1)}%</strong> mean absolute percentage error versus <strong>{number(estate.national_validation?.mean_ape,1)}%</strong> for the island equation. {localBetter?'The local fit improves this particular holdout.':'The island equation performs at least as well; a separate local fit adds no demonstrated benefit here.'}</p>}{estate.test_unseen_type_n>0&&<p>{estate.test_unseen_type_n} later sales of flat types absent from local training are excluded from this paired comparison.</p>}{estate.warnings.map(warning=><p className="model-warning" key={warning}><Info size={15}/>{warning}</p>)}</div>}
      <div className="model-section"><h3>How the recorded relationships differ</h3><p>Estimated price differences with other included predictors held fixed. Intervals are approximate 95% coefficient intervals, clustered by block; overlapping intervals alone do not establish whether two estate effects differ.</p><div className="reference-table" role="region" tabIndex={0} aria-label="National and estate coefficient comparison"><table><thead><tr><th>Comparison</th><th>Island association</th><th>Island interval</th>{local&&<><th>{titleCase(estate.town)} association</th><th>Local interval</th></>}</tr></thead><tbody>{factors.map(([key,label,step])=><tr key={key}><td>{label}</td><td>{signed(effect(national.coefficients[key],step),1)}%</td><td>{interval(national,key,step)}</td>{local&&<><td>{signed(effect(local.coefficients[key],step),1)}%</td><td>{interval(local,key,step)}</td></>}</tr>)}</tbody></table></div></div>
      <div className="model-section"><h3>Which factors does {estate&&local?titleCase(estate.town):'the island model'} rely on?</h3><p>{top?`${top.label} has the largest positive removal penalty in this model. `:''}Each bar shows the increase in later-sale mean percentage error after removing a factor and refitting. Bigger positive values indicate more useful predictive information; negative values mean removing the factor helped on this test period. Values are percentage points, not price premiums.</p><Importance model={local||national}/></div>
      <div className="model-section model-explanation"><h3>Why different estates can have different anchors</h3>{local&&<p>In {titleCase(estate.town)}, the middle half of training sales spans <strong>{number(local.support.area.p25)}–{number(local.support.area.p75)} m²</strong> and <strong>{number(local.support.lease.p25,1)}–{number(local.support.lease.p75,1)} remaining lease years</strong>. That local mix determines which differences the model has enough evidence to distinguish.</p>}<p>An estate with similar-age flats has little lease variation to learn from. Where older flats and newer projects coexist, lease may separate distinct segments—but it may also stand in for unmeasured project quality or location. Area and flat type overlap, so they are tested together. Storey can reflect views and building differences that are not directly recorded.</p><p>A national equation pools evidence and can be more stable in smaller estates. Local equations allow different relationships, but can overfit or change with the homes sold. School access, transport convenience and amenity quality are plausible explanations to investigate; the current equations do not measure them.</p></div>
      <details className="model-audit"><summary>All estate comparisons and model audit</summary><div className="reference-table" role="region" tabIndex={0} aria-label="All estate model validation results"><table><thead><tr><th>Estate</th><th>Train sales</th><th>Local test error</th><th>Island test error on same sales</th><th>Most useful recorded factor</th></tr></thead><tbody>{report.towns.map(row=><tr key={row.town}><td><button className="text-button" onClick={()=>onSelectTown(row.town)}>{titleCase(row.town)}</button></td><td>{number(row.training_n)}</td><td>{row.model?number(row.model.validation?.mean_ape,1)+'%':'Pooled only'}</td><td>{number(row.national_validation?.mean_ape,1)}%</td><td>{row.model?.importance.find(item=>item.error_increase_pp>0)?.label||'No independent local fit'}</td></tr>)}</tbody></table></div><ul>{report.notes.map(note=><li key={note}>{note}</li>)}</ul><p>Excluded from the 36-month window: {number(report.excluded.rare_flat_types||0)} rare flat types; {number(report.excluded.invalid_or_missing_fields||0)} incomplete or invalid rows. Model generated {report.generated_at.slice(0,10)}.</p></details>
    </>}
  </section>;
}
