/* Optional QA tool; runtime apps require neither Node nor Playwright. */
const fs=require('fs'),path=require('path'),assert=require('assert/strict');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const base=process.env.ATLAS_BASE||'http://127.0.0.1:8874/';
const output=process.env.ATLAS_QA_OUTPUT||'/tmp/open-atlas-qa';
(async()=>{
 fs.mkdirSync(output,{recursive:true});let checks=[];
 const browser=await chromium.launch({headless:true,executablePath:process.env.BROWSER_EXECUTABLE});
 try{
 const c=await browser.newContext({viewport:{width:1440,height:1100}}),p=await c.newPage(),errors=[],external=[];
 p.on('pageerror',e=>errors.push(e.message));p.on('request',r=>{if(!r.url().startsWith(base)&&!r.url().startsWith('data:'))external.push(r.url())});
 const check=(name,fn)=>{fn();checks.push(name)};
 await p.goto(base);await p.screenshot({path:path.join(output,'home.png'),fullPage:true});assert((await p.locator('a[href="demo/"]').count())>0);assert.equal(await p.locator('a[href="https://github.com/SJAH9/open-atlas-standard/generate"]').count(),1);checks.push('Homepage exposes demo and template');
 await p.goto(base+'library.html');await p.locator('#query').fill('water');assert((await p.locator('.library article:not([hidden])').count())<46);assert((await p.locator('.library article:not([hidden])').count())>0);checks.push('Source library search');
 await p.goto(base+'demo/?entity=FRA&metric=rtlp&period=2026');await p.waitForFunction(()=>!!window.OpenAtlas);
 check('Shared view honored',()=>assert.equal(new URL(p.url()).searchParams.get('metric'),'rtlp'));
 assert.equal(await p.locator('#inspector h2').textContent(),'France');assert(await p.locator('#inspector').textContent().then(t=>t.includes('modeled')));checks.push('Country inspector retains model state');
 await p.selectOption('#metric','life-support');assert(await p.locator('#inspector').textContent().then(t=>t.includes('Not measured')&&t.includes('no accepted observations')));checks.push('Missing life support is not zero');
 await p.selectOption('#metric','population');await p.selectOption('#period','2024');await p.selectOption('#projection','equal-area');await p.waitForFunction(()=>document.querySelector('#map svg').getAttribute('viewBox').includes('636.6'));checks.push('Exact-period selection and projection');
 await p.getByRole('button',{name:'Register',exact:true}).click();await p.locator('#search').fill('tuvalu');assert.equal(await p.locator('#register tbody tr').count(),1);await p.locator('#register tbody button').click();assert.equal(await p.locator('#inspector h2').textContent(),'Tuvalu');checks.push('Small state without polygon remains accessible');
 await p.getByRole('button',{name:'Settings',exact:true}).click();await p.selectOption('#theme-setting','dark');assert.equal(await p.locator('html').getAttribute('data-theme'),'dark');await p.mouse.click(1,1);assert.equal(await p.locator('#settings').isVisible(),false);await p.getByRole('button',{name:'Day',exact:true}).click();checks.push('Day/night and outside-click settings');
 await p.locator('#fullscreen').click();assert(await p.evaluate(()=>!!document.fullscreenElement));await p.keyboard.press('Escape');if(await p.evaluate(()=>!!document.fullscreenElement))await p.evaluate(()=>document.exitFullscreen());checks.push('Single fullscreen control');
 await p.selectOption('#metric','capital-exclusions');await p.selectOption('#entity','CHN');assert(await p.locator('#inspector .value').evaluate(e=>e.scrollWidth<=e.clientWidth));await p.screenshot({path:path.join(output,'atlas-desktop.png'),fullPage:true});
 await p.evaluate(async()=>{await navigator.serviceWorker.ready});await p.reload();await p.waitForFunction(()=>!!window.OpenAtlas);await c.setOffline(true);await p.reload();await p.waitForFunction(()=>!!window.OpenAtlas);assert(await p.locator('#inspector').textContent().then(t=>t.includes('China')));await c.setOffline(false);checks.push('Offline shared-view reload');
 const mobile=await browser.newContext({viewport:{width:390,height:844},isMobile:true,hasTouch:true,deviceScaleFactor:1}),m=await mobile.newPage();m.on('pageerror',e=>errors.push(e.message));await m.goto(base+'demo/?metric=population&period=2025&entity=FRA');await m.waitForFunction(()=>!!window.OpenAtlas);assert(await m.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));await m.screenshot({path:path.join(output,'atlas-mobile.png'),fullPage:true});checks.push('390px layout no horizontal overflow');
 await p.goto(base+'events/');await p.waitForFunction(()=>!!window.OpenAtlas);const first=await p.evaluate(()=>OpenAtlas.bundle.observations[0].entity);await p.selectOption('#entity',first);assert(await p.locator('#inspector').textContent().then(t=>t.includes('Rollup eligible')&&t.includes('false')));assert((await p.locator('#map circle').count())>0);await p.screenshot({path:path.join(output,'events.png'),fullPage:true});checks.push('Event precision and non-rollup inspector');
 check('No JavaScript errors',()=>assert.deepEqual(errors,[]));check('No third-party runtime requests',()=>assert.deepEqual(external,[]));
 fs.writeFileSync(path.join(output,'report.json'),JSON.stringify({base,checks,passed:checks.length,errors,external},null,2));console.log(JSON.stringify({base,checks,passed:checks.length,output},null,2));
 await c.close();await mobile.close();
 }finally{await browser.close()}
})().catch(e=>{console.error(e);process.exitCode=1});
