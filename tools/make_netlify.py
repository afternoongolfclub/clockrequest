"""Build the Netlify edition of the Clock Request Desk from the artifact source.

Same design, geometry and live preview. What changes:
  - no claude.use() capabilities; the page is plain static HTML
  - the order form posts to Netlify Forms, crest file included
  - the admin Requests and Costing tabs are removed (cost and margin
    figures must not ship to a public site)
"""
import json, os, re, shutil, sys

SRC = '/home/claude/work/app_template.html'
DEST = '/home/claude/work/netlify-site'


def cut(s, start, end, repl):
    i = s.index(start)
    j = s.index(end, i)
    return s[:i] + repl + s[j:]


def main():
    t = open(SRC).read()

    # ---- head: real document, not the artifact skeleton -----------------
    t = t.replace('<meta name="claude:viewport-fit-sides" content="cover">', '')

    # ---- strip the admin tab bar and its panes --------------------------
    t = cut(t, '    <div class="topnav" role="tablist"', '    </div>\n  </header>', '')
    t = cut(t, '  <div id="paneInbox"', '  <div id="paneCost"', '')
    t = cut(t, '  <div id="paneCost"', '  <footer class="foot">', '')

    # ---- order fields become real form fields ---------------------------
    for fid, nm in [('fClub', 'club'), ('fContact', 'contact'), ('fEmail', 'email'),
                    ('fPhone', 'phone'), ('fQty', 'quantity'), ('fDue', 'needed_by'),
                    ('fNotes', 'notes')]:
        t = t.replace('id="%s"' % fid, 'id="%s" name="%s"' % (fid, nm))
    t = t.replace('id="logoFile"', 'id="logoFile" name="crest"')

    # ---- wrap crest + filament + order in one Netlify form --------------
    crest_open = '      <section class="card">\n        <div class="cardhead"><span class="step">03</span><h2>Crest</h2></div>'
    assert crest_open in t, 'crest section anchor not found'
    hidden = '\n'.join(
        '        <input type="hidden" name="%s" id="h_%s">' % (n, n) for n in
        ['layout', 'crown_line_1', 'crown_line_2', 'lower_arc', 'dial_text',
         'dial_line_1', 'dial_line_2', 'filament_housing', 'filament_accents',
         'filament_dial', 'filament_numerals', 'spec'])
    t = t.replace(crest_open,
                  '      <form name="clock-request" method="POST" data-netlify="true"\n'
                  '            data-netlify-honeypot="bot-field" enctype="multipart/form-data"\n'
                  '            action="/thanks.html" id="orderForm">\n'
                  '        <input type="hidden" name="form-name" value="clock-request">\n'
                  '        <p hidden><label>Leave this empty: <input name="bot-field"></label></p>\n'
                  + hidden + '\n\n' + crest_open)
    t = t.replace('<form id="orderForm" novalidate>', '<div>')
    t = t.replace('          </div>\n        </form>\n      </section>',
                  '          </div>\n        </div>\n      </section>\n      </form>')

    # ---- layout picker: buttons, not radios (radios would post a stray field)
    t = cut(t, 'function layoutGlyph(id){', 'function buildFields(){', '''function layoutGlyph(id){
  var a='stroke="currentColor" fill="none" stroke-width="1.4" stroke-linecap="round"';
  var base='<svg class="glyph" viewBox="0 0 64 40" aria-hidden="true" style="color:var(--muted)">'+
    '<circle cx="32" cy="22" r="12" '+a+'/>';
  if(id==="stacked") base+='<path d="M14 11 A22 22 0 0 1 50 11" '+a+'/><path d="M17 15.5 A19 19 0 0 1 47 15.5" '+a+'/><path d="M22 36 A16 16 0 0 0 42 36" '+a+'/>';
  if(id==="dial")    base+='<path d="M14 11 A22 22 0 0 1 50 11" '+a+'/><path d="M22 36 A16 16 0 0 0 42 36" '+a+'/><path d="M25 24 h14 M27 28 h10" '+a+'/>';
  if(id==="single")  base+='<path d="M14 11 A22 22 0 0 1 50 11" '+a+'/><path d="M22 36 A16 16 0 0 0 42 36" '+a+'/>';
  return base+'</svg>';
}
function buildLayouts(){
  var h="";
  LAYOUTS.forEach(function(L){
    h+='<button type="button" class="lay" data-lay="'+L.id+'" aria-pressed="'+(S.layout===L.id?"true":"false")+'">'+
       '<span class="box">'+layoutGlyph(L.id)+
       '<span class="nm">'+esc(L.name)+'</span><span class="ds">'+esc(L.desc)+'</span></span></button>';
  });
  $("layouts").innerHTML=h;
  Array.prototype.forEach.call($("layouts").querySelectorAll(".lay"),function(b){
    b.addEventListener("click",function(){
      S.layout=b.getAttribute("data-lay");
      Array.prototype.forEach.call($("layouts").querySelectorAll(".lay"),function(o){
        o.setAttribute("aria-pressed", o===b ? "true":"false"); });
      buildFields(); render();
    });
  });
}

/* ---------- lettering fields ---------- */
var LIMITS={topA:28,topB:28,bottom:18,year:14,dialA:18,dialB:18};
''')
    t = t.replace('''.lay{display:block;position:relative;cursor:pointer;min-width:0}
.lay input{position:absolute;inset:0;width:100%;height:100%;opacity:0;margin:0;cursor:pointer}
.lay .box{display:block;border:1px solid var(--rule);border-radius:11px;padding:12px;background:var(--sunk);height:100%;pointer-events:none}
.lay input:checked+.box{border-color:var(--brass);background:var(--brass-wash);box-shadow:inset 0 0 0 1px var(--brass)}
.lay input:focus-visible+.box{outline:2px solid var(--brass);outline-offset:2px}''',
'''.lay{display:block;position:relative;cursor:pointer;min-width:0;padding:0;border:0;background:none;
  font:inherit;color:inherit;text-align:left;width:100%}
.lay .box{display:block;border:1px solid var(--rule);border-radius:11px;padding:12px;background:var(--sunk);height:100%}
.lay[aria-pressed="true"] .box{border-color:var(--brass);background:var(--brass-wash);box-shadow:inset 0 0 0 1px var(--brass)}
.lay:focus-visible .box{outline:2px solid var(--brass);outline-offset:2px}''')

    # ---- replace every capability-backed block with the Netlify submit ---
    t = cut(t, '/* ---------- tabs ---------- */', '/* ---------- go ---------- */', '''/* ---------- submit through Netlify Forms ---------- */
function msg(t,cls){ var m=$("sendMsg"); m.textContent=t; m.className="submitmsg"+(cls?" "+cls:""); }
function specText(){
  var L=LAYOUTS.filter(function(x){return x.id===S.layout;})[0], out=[];
  out.push("Layout: "+L.name);
  L.fields.forEach(function(k){ if(S[k]) out.push(L.labels[k]+": "+S[k]); });
  SLOTS.forEach(function(s){
    var f=S.fil[s.key];
    out.push(s.role+": "+f.name+" ("+f.series+" "+f.hex+")");
  });
  if(S.logoName) out.push("Crest file: "+S.logoName);
  return out.join("\\n");
}
function syncHidden(){
  var L=LAYOUTS.filter(function(x){return x.id===S.layout;})[0];
  var map={layout:L.name, crown_line_1:"", crown_line_2:"", lower_arc:"",
           dial_text:"", dial_line_1:"", dial_line_2:""};
  if(S.layout==="stacked"){ map.crown_line_1=S.topA; map.crown_line_2=S.topB; }
  else { map.crown_line_1=S.topA; }
  map.lower_arc=S.bottom; map.dial_text=S.year;
  if(S.layout==="dial"){ map.dial_line_1=S.dialA; map.dial_line_2=S.dialB; }
  map.filament_housing=S.fil.body.series+" "+S.fil.body.name+" "+S.fil.body.hex;
  map.filament_accents=S.fil.accent.series+" "+S.fil.accent.name+" "+S.fil.accent.hex;
  map.filament_dial=S.fil.dial.series+" "+S.fil.dial.name+" "+S.fil.dial.hex;
  map.filament_numerals=S.fil.numeral.series+" "+S.fil.numeral.name+" "+S.fil.numeral.hex;
  map.spec=specText();
  Object.keys(map).forEach(function(k){ var el=$("h_"+k); if(el) el.value=map[k]; });
}
$("orderForm").addEventListener("submit",function(e){
  var email=$("fEmail").value.trim(), club=$("fClub").value.trim();
  if(!club){ e.preventDefault(); msg("Add the club or organisation so the request can be matched up.","bad"); $("fClub").focus(); return; }
  if(!email || email.indexOf("@")<1){ e.preventDefault(); msg("Add an email so there's a way to reply.","bad"); $("fEmail").focus(); return; }
  syncHidden();
  msg("Sending\\u2026");
  $("sendBtn").disabled=true;
  /* let the browser post it: Netlify takes the multipart body, crest included */
});

''')
    t = t.replace('  if(document.fonts && document.fonts.ready) document.fonts.ready.then(render);',
                  '  if(document.fonts && document.fonts.ready) document.fonts.ready.then(render);\n'
                  '  syncHidden();')
    # keep hidden fields current as the person works
    t = t.replace('  renderChips();', '  renderChips();\n  try{ syncHidden(); }catch(e){}')

    # ---- copy that no longer applies -----------------------------------
    t = t.replace("Drop a PNG, JPEG or SVG here, or choose a file. 20 MB limit.",
                  "Drop a PNG, JPEG or SVG here, or choose a file. It is sent with the request.")
    t = t.replace("Set the lettering, send a crest, and choose filament. The preview is drawn from the real printed geometry, so what you see is what the plate cuts.",
                  "Set the lettering, send a crest, and choose filament. The preview is drawn from the real printed geometry, so what you see is what the plate cuts.")

    assert 'claude.use' not in t, 'capability call still present'
    assert 'window.claude' not in t, 'window.claude still present'
    assert 'tabInbox' not in t and 'tabCost' not in t, 'admin tab remnant'
    assert 'COST' not in t, 'costing remnant'

    # ---- write the site -------------------------------------------------
    if os.path.exists(DEST):
        shutil.rmtree(DEST)
    os.makedirs(DEST)
    G = json.load(open('/home/claude/work/geom.json'))
    body = t.replace('__GEOM__', json.dumps(G, separators=(',', ':')).replace('<', '\\u003c'))
    body = body.replace('__FONT__', open('/home/claude/work/cal.b64').read().strip())
    head = ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">\n'
            '<meta name="description" content="Order a custom branded golf-club clock: lettering, crest and Bambu Lab filament, with a live preview drawn from the real print geometry.">\n'
            '<style>:root{color-scheme:light}html,body{margin:0}img{max-width:100%}[hidden]{display:none!important}</style>\n'
            '</head>\n<body>\n')
    open(DEST + '/index.html', 'w').write(head + body + '\n</body>\n</html>\n')
    print('index.html %.1f KB' % (os.path.getsize(DEST + '/index.html') / 1024))
    return DEST


if __name__ == '__main__':
    main()
