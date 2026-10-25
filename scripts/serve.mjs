import http from 'node:http';
import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../_site');
const mime = {'.html':'text/html; charset=utf-8','.css':'text/css; charset=utf-8','.js':'text/javascript; charset=utf-8','.json':'application/json; charset=utf-8','.webp':'image/webp','.png':'image/png','.gif':'image/gif','.svg':'image/svg+xml'};
http.createServer(async (req,res)=>{
  try {
    const url = new URL(req.url,'http://127.0.0.1');
    let relative = decodeURIComponent(url.pathname);
    if(relative==='/AI-Art') {res.writeHead(302,{Location:'/AI-Art/'});res.end();return;}
    if(relative.startsWith('/AI-Art/'))relative=relative.slice(7);
    if(relative.endsWith('/'))relative+='index.html';
    const file = path.resolve(root,'.'+relative);
    if(!file.startsWith(root+path.sep)){res.writeHead(403);res.end();return;}
    const bytes=await fs.readFile(file);
    res.writeHead(200,{'Content-Type':mime[path.extname(file)]||'application/octet-stream','Cache-Control':'no-cache'});res.end(bytes);
  } catch {res.writeHead(404);res.end('Not found');}
}).listen(4173,'127.0.0.1',()=>console.log('Catalog: http://127.0.0.1:4173/AI-Art/'));
