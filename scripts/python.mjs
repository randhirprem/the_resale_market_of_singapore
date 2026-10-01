// Resolve a usable Python 3 interpreter even when PATH contains a stale installation.
import {spawn,spawnSync} from 'node:child_process';
const candidates=[process.env.HDB_PYTHON,'python3','python3.11','python','/usr/bin/python3'].filter(Boolean);
const executable=candidates.find(candidate=>{
  const probe=spawnSync(candidate,['-c','import sys; sys.exit(0 if sys.version_info >= (3,9) else 1)'],{stdio:'ignore'});
  return !probe.error&&probe.status===0;
});
if(!executable){console.error('Python 3.9+ is required. Install it or set HDB_PYTHON to its executable path.');process.exit(1);}
const child=spawn(executable,process.argv.slice(2),{stdio:'inherit'});
for(const signal of ['SIGINT','SIGTERM'])process.on(signal,()=>child.kill(signal));
child.on('error',error=>{console.error(error.message);process.exitCode=1;});
child.on('exit',code=>{process.exitCode=code??1;});
