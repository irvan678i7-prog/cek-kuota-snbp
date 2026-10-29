#!/usr/bin/env python3
"""Best-effort browser extraction of official SNPMB programme table.
Never fabricate quotas. Retain existing verified records if scraping fails.
"""
import asyncio, json, os, re, datetime
from pathlib import Path
from playwright.async_api import async_playwright
SOURCE="https://www.snpmb.id/snbp/daya-tampung-snbp"
OUT=Path("data/snbp.json")
def as_int(s):
    s=str(s).strip().replace(".","").replace(",","")
    m=re.search(r"\d+",s)
    return int(m.group()) if m else None
def extract_rows(rows,ptn,year=2026):
    collected=[]
    for cells in rows:
        cells=[re.sub(r"\s+"," ",str(x)).strip() for x in cells]
        if len(cells)<5 or not cells[0].isdigit():continue
        # Official columns: No | Kode | Program Studi | Jenjang | Daya Tampung | Portofolio
        if len(cells)<6 or not re.fullmatch(r"\d+",cells[1]):continue
        cap=as_int(cells[4])
        if cap is None or cap<0 or cap>10000:continue
        name=cells[2]
        if not name or len(name)>160:continue
        collected.append(dict(tahun=year,ptn=ptn,prodi=name,kode_prodi=cells[1],
                              jenjang=cells[3],daya_tampung=cap,peminat=None))
    return collected
async def main():
    before=json.loads(OUT.read_text()) if OUT.exists() else {"data":[]}
    saved={(str(x.get("tahun")),str(x.get("ptn")),str(x.get("kode_prodi") or x.get("prodi"))):x
           for x in before.get("data",[]) if isinstance(x,dict)}
    errors=[]; counts=[]
    async with async_playwright() as p:
        browser=await p.chromium.launch(headless=True,args=["--no-sandbox"])
        page=await browser.new_page(viewport={"width":1440,"height":1000},locale="id-ID")
        try:
            await page.goto(SOURCE,wait_until="domcontentloaded",timeout=65000)
            await page.wait_for_timeout(4500)
            # Inspect all document elements for an institution code plus name;
            # click the smallest ancestor that responds as a card/button.
            targets=await page.evaluate("""() => {
              const nodes=[...document.querySelectorAll('button,[role=button],li,article')];
              let found=[];
              for(let node of nodes) {
                let t=(node.innerText||'').trim().replace(/\\s+/g,' ');
                let m=t.match(/^(.{5,110}?)\\s+(\\d{4})$/);
                if(m && !/^(DAFTAR|SEMUA|PTN |CARI)/i.test(m[1])) found.push({name:m[1],code:m[2]});
              }
              return [...new Map(found.map(x=>[x.code,x])).values()];
            }""")
            print("Found PTNs:",len(targets))
            if not targets:
                raise RuntimeError("No clickable PTN cards found; website selectors may have changed")
            for idx,target in enumerate(targets):
                name,code=target["name"],target["code"]
                try:
                    # Text-based locator, avoids dependency on CSS class names.
                    candidates=page.locator("button,[role=button],li,article").filter(has_text=code)
                    clicked=False
                    for j in range(min(await candidates.count(),12)):
                        loc=candidates.nth(j)
                        txt=re.sub(r"\s+"," ",await loc.inner_text()).strip()
                        if txt.endswith(code) and name.lower() in txt.lower() and len(txt)<170:
                            await loc.click(timeout=6000)
                            clicked=True
                            break
                    if not clicked:raise RuntimeError("Unable to click PTN card")
                    try:
                        await page.wait_for_function("""() => {
                          let rows=[...document.querySelectorAll('table tbody tr')];
                          return rows.some(r=>r.querySelectorAll('td').length>=5);
                        }""",timeout=18000)
                    except Exception:pass
                    await page.wait_for_timeout(600)
                    raw=await page.locator("table tbody tr").evaluate_all("""rs=>rs.map(
                      r=>[...r.querySelectorAll('td')].map(c=>(c.innerText||'').trim())
                    )""")
                    items=extract_rows(raw,name)
                    for x in items:saved[(str(x["tahun"]),x["ptn"],x["kode_prodi"])]=x
                    counts.append([name,len(items)])
                    print(f"{idx+1}/{len(targets)} {name}: {len(items)} programs",flush=True)
                except Exception as exc:errors.append(f"{name}: {exc}")
        finally:
            await browser.close()
    data=sorted(saved.values(),key=lambda x:(str(x.get("ptn")),str(x.get("prodi")),str(x.get("tahun"))))
    updated={"data":data,"source":SOURCE,"updated_at":datetime.datetime.now(datetime.timezone.utc).isoformat(),
             "collection_method":"Automated browser reading official public SNPMB programme table",
             "scrape_summary":{"ptn_scanned":len(counts),"ptn_with_records":sum(bool(n) for _,n in counts),
                               "errors":errors[:12]}}
    if not any(n for _,n in counts):
        print("No validated programs extracted; keeping existing data unmodified")
        return
    OUT.write_text(json.dumps(updated,ensure_ascii=False,indent=2)+"\n")
    print("Programs in dataset:",len(data))
if __name__=="__main__":asyncio.run(main())
