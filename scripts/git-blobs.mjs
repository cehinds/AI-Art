import { spawn } from 'node:child_process';
import { ROOT } from './lib.mjs';

// A single process serves queued requests. Only one encoded blob is buffered at
// a time; callers control the number of decoded images they retain concurrently.
export class GitBlobReader {
  constructor(root=ROOT,{maxBlobBytes=512*1024*1024}={}) {
    this.child=spawn('git',['cat-file','--batch'],{cwd:root,stdio:['pipe','pipe','pipe'],windowsHide:true});
    this.iterator=this.child.stdout[Symbol.asyncIterator]();
    this.buffer=Buffer.alloc(0);this.tail=Promise.resolve();this.closed=false;this.maxBlobBytes=maxBlobBytes;this.stderr='';
    this.child.stderr.on('data',chunk=>{this.stderr=(this.stderr+chunk.toString()).slice(-8192);});
    this.child.stdin.on('error',()=>{});
    this.child.on('error',error=>{this.processError=error;});
    this.finished=new Promise(resolve=>this.child.once('close',code=>resolve(code)));
  }
  async more() {
    const {value,done}=await this.iterator.next();
    if(done) throw this.processError||new Error(`Git blob stream ended unexpectedly: ${this.stderr}`);
    this.buffer=value;
  }
  async line() {
    const pieces=[];let length=0;
    while(true) {
      if(!this.buffer.length) await this.more();
      const end=this.buffer.indexOf(10);
      if(end>=0) {pieces.push(this.buffer.subarray(0,end));this.buffer=this.buffer.subarray(end+1);return Buffer.concat(pieces).toString('ascii');}
      pieces.push(this.buffer);length+=this.buffer.length;this.buffer=Buffer.alloc(0);
      if(length>1024) throw new Error('Invalid Git blob header');
    }
  }
  async exact(length) {
    const output=Buffer.allocUnsafe(length);let offset=0;
    while(offset<length) {
      if(!this.buffer.length) await this.more();
      const take=Math.min(length-offset,this.buffer.length);
      this.buffer.copy(output,offset,0,take);offset+=take;this.buffer=this.buffer.subarray(take);
    }
    return output;
  }
  read(blob) {
    if(this.closed) return Promise.reject(new Error('Git blob reader is closed'));
    if(!/^[a-f0-9]{40}$/.test(blob)) return Promise.reject(new Error(`Invalid Git blob ID: ${blob}`));
    const request=this.tail.then(async()=>{
      this.child.stdin.write(`${blob}\n`);
      const header=await this.line();
      if(header===`${blob} missing`) throw new Error(`Missing Git blob: ${blob}`);
      const [actual,type,sizeText]=header.split(' ');const size=Number(sizeText);
      if(actual!==blob||type!=='blob'||!Number.isSafeInteger(size)||size<0||size>this.maxBlobBytes) {
        this.child.kill();throw new Error(`Invalid or oversized Git blob response: ${header}`);
      }
      const bytes=await this.exact(size);
      if((await this.exact(1))[0]!==10) {this.child.kill();throw new Error('Invalid Git blob terminator');}
      return bytes;
    });
    this.tail=request.catch(()=>{});
    return request;
  }
  async close() {
    if(this.closed) return;
    this.closed=true;await this.tail;this.child.stdin.end();await this.finished;
  }
}
