"""Build the Netlify edition of the Clock Request Desk from the artifact source.

Same design and the same rendered post-clock preview. What changes:
  - no claude.use() capabilities; the page is plain static HTML
  - the order form posts to Netlify Forms, crest file included
  - the admin Requests and Costing tabs are removed (cost and margin
    figures must not ship to a public site)

Usage:  python3 tools/make_netlify.py [DEST_DIR]      (default: repo root)
Only DEST_DIR/index.html is written. The preview's static assets
(post_geom.json, shade_*/mask_*.png, assembly.html, manifest_*.json,
meshes_*.b64.txt) live in the repo root alongside it.
"""
import os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, 'app_template.html')


def cut(s, start, end, repl):
    i = s.index(start)
    j = s.index(end, i)
    return s[:i] + repl + s[j:]


def must_replace(s, old, new):
    assert old in s, 'anchor not found: %r' % old[:70]
    return s.replace(old, new)


HIDDEN = ['clock', 'club_name', 'lower_line', 'filament_housing',
          'filament_accents', 'filament_dial', 'filament_numerals', 'spec']


def build(t):
    # ---- strip the artifact skeleton; a real <head> is added below --------
    t = t[t.index('<body>') + len('<body>'):].lstrip('\n')
    t = t[:t.rindex('</body>')].rstrip() + '\n'
    title = '<title>Clock Request Desk</title>\n'
    t = must_replace(t, title, '')
    t = must_replace(t, '<meta name="claude:viewport-fit-sides" content="cover">\n', '')

    # ---- strip the admin tab bar and its panes ----------------------------
    t = cut(t, '    <div class="topnav" role="tablist"', '  </header>', '')
    t = cut(t, '  <div id="paneInbox"', '  <div id="paneCost"', '')
    t = cut(t, '  <div id="paneCost"', '  <footer class="foot">', '')

    # ---- order fields become real form fields -----------------------------
    for fid, nm in [('fClub', 'club'), ('fContact', 'contact'), ('fEmail', 'email'),
                    ('fPhone', 'phone'), ('fQty', 'quantity'), ('fDue', 'needed_by'),
                    ('fNotes', 'notes')]:
        t = must_replace(t, 'id="%s"' % fid, 'id="%s" name="%s"' % (fid, nm))
    t = must_replace(t, 'id="logoFile"', 'id="logoFile" name="crest"')

    # ---- wrap crest + filament + order in one Netlify form ----------------
    i = t.index('<h2>Crest</h2>')
    crest_open = t.rindex('      <section class="card">', 0, i)
    hidden = '\n'.join('        <input type="hidden" name="%s" id="h_%s">' % (n, n) for n in HIDDEN)
    t = (t[:crest_open] +
         '      <form name="clock-request" method="POST" data-netlify="true"\n'
         '            data-netlify-honeypot="bot-field" enctype="multipart/form-data"\n'
         '            action="/thanks.html" id="orderForm">\n'
         '        <input type="hidden" name="form-name" value="clock-request">\n'
         '        <p hidden><label>Leave this empty: <input name="bot-field"></label></p>\n'
         + hidden + '\n\n' + t[crest_open:])
    t = must_replace(t, '<form id="orderForm" novalidate>', '<div>')
    t = must_replace(t, '          </div>\n        </form>\n      </section>',
                     '          </div>\n        </div>\n      </section>\n      </form>')

    # ---- replace every capability-backed block with the Netlify submit ----
    t = cut(t, '/* ---------- tabs ---------- */', '/* ---------- go ---------- */', r'''/* ---------- submit through Netlify Forms ---------- */
function msg(t,cls){ var m=$("sendMsg"); m.textContent=t; m.className="submitmsg"+(cls?" "+cls:""); }
function styleName(){ var s=STYLES.filter(function(x){return x.id===S.style;})[0]; return s?s.name:S.style; }
function filTxt(f){ return f.series+" "+f.name+" "+f.hex; }
function specText(){
  var out=["Clock: "+styleName()];
  POST_LAYOUT.fields.forEach(function(k){ if(S[k]) out.push(POST_LAYOUT.labels[k]+": "+S[k]); });
  SLOTS.forEach(function(s){
    var f=S.fil[s.key];
    out.push(s.role+": "+f.name+" ("+f.series+" "+f.hex+")");
  });
  if(S.logoName) out.push("Crest file: "+S.logoName);
  return out.join("\n");
}
function syncHidden(){
  var map={clock:styleName(), club_name:S.topA||"", lower_line:S.bottom||"",
    filament_housing:filTxt(S.fil.body), filament_accents:filTxt(S.fil.accent),
    filament_dial:filTxt(S.fil.dial), filament_numerals:filTxt(S.fil.numeral),
    spec:specText()};
  Object.keys(map).forEach(function(k){ var el=$("h_"+k); if(el) el.value=map[k]; });
}
/* a dropped crest has to land in the file input, or it never posts */
$("drop").addEventListener("drop",function(e){
  try{ if(e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files.length && pendingFile===e.dataTransfer.files[0])
         $("logoFile").files=e.dataTransfer.files; }catch(err){}
});
$("orderForm").addEventListener("submit",function(e){
  var email=$("fEmail").value.trim(), club=$("fClub").value.trim();
  if(!club){ e.preventDefault(); msg("Add the club or organisation so the request can be matched up.","bad"); $("fClub").focus(); return; }
  if(!email || email.indexOf("@")<1){ e.preventDefault(); msg("Add an email so there's a way to reply.","bad"); $("fEmail").focus(); return; }
  syncHidden();
  msg("Sending…");
  $("sendBtn").disabled=true;
  /* let the browser post it: Netlify takes the multipart body, crest included */
});

''')
    t = must_replace(t, '    renderPost(); renderChips();\n',
                     '    renderPost(); renderChips();\n    try{ syncHidden(); }catch(e){}\n')
    t = must_replace(t, 'if(document.fonts && document.fonts.ready) document.fonts.ready.then(render);\n',
                     'if(document.fonts && document.fonts.ready) document.fonts.ready.then(render);\n'
                     'syncHidden();\n')

    # ---- crest size: Netlify Forms caps a submission at 8 MB ---------------
    t = must_replace(t, 'if(file.size>20*1024*1024){\n    $("logoHelp").textContent="That file is over the 20 MB limit."; return;',
                     'if(file.size>8*1024*1024){\n    $("logoHelp").textContent="That file is over the 8 MB limit."; return;')
    t = t.replace("Drop a PNG, JPEG or SVG here, or choose a file. 20 MB limit.",
                  "Drop a PNG, JPEG or SVG here, or choose a file. 8 MB limit; it is sent with the request.")

    assert 'claude.use' not in t, 'capability call still present'
    assert 'window.claude' not in t, 'window.claude still present'
    assert 'tabInbox' not in t and 'tabCost' not in t, 'admin tab remnant'
    assert 'COST' not in t, 'costing remnant'
    assert 'paneInbox' not in t and 'paneCost' not in t, 'admin pane remnant'
    assert t.count('<form') == 1 and t.count('</form>') == 1, 'form nesting off'

    head = ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">\n'
            '<title>Clock Request Desk</title>\n'
            '<meta name="description" content="Order a custom branded golf post clock: lettering, crest and Bambu Lab filament, with a live preview rendered from the real print files.">\n'
            '<style>:root{color-scheme:light}html,body{margin:0}img{max-width:100%}[hidden]{display:none!important}</style>\n'
            '</head>\n<body>\n')
    return head + t + '</body>\n</html>\n'


def main():
    dest = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(HERE)
    out = build(open(SRC, encoding='utf-8').read())
    path = os.path.join(dest, 'index.html')
    open(path, 'w', encoding='utf-8').write(out)
    print('%s %.1f KB' % (path, os.path.getsize(path) / 1024))


if __name__ == '__main__':
    main()
