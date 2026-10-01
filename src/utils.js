export const number = (value, digits=0) => value == null ? '—' : Number(value).toLocaleString('en-SG',{maximumFractionDigits:digits});
export const money = value => value == null ? '—' : '$'+number(value);
export const compact = value => value == null ? '—' : value >= 1e6 ? '$'+(value/1e6).toFixed(2)+'M' : '$'+number(value/1000,1)+'k';
export const titleCase = text => text.toLowerCase().replace(/\b\w/g,c=>c.toUpperCase());
export const monthLabel = month => new Date(month+'-01T00:00:00').toLocaleDateString('en-SG',{month:'short',year:'numeric'});
export const queryString = filters => new URLSearchParams(Object.entries(filters).filter(([,v])=>v!=='' && v!=null)).toString();
export async function getJSON(url, signal) {
  const response=await fetch(url,{signal});
  const result=await response.json();
  if(!response.ok) throw new Error(result.error || 'Unable to load data. Please try again.');
  return result;
}
export const colors=['#3ee7d4','#a88aff','#f05eb9','#78a8ff','#eacc67','#fd9270','#a5b8c7'];
