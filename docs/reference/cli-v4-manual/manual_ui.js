const cards=[...document.querySelectorAll('.capability')];
const search=document.querySelector('#search');
const report=document.querySelector('#search-status');
function filterCards(){const q=search.value.trim().toLocaleLowerCase();let n=0;for(const card of cards){card.hidden=!card.dataset.search.toLocaleLowerCase().includes(q);if(!card.hidden)n++;}for(const group of document.querySelectorAll('.scenario'))group.hidden=![...group.querySelectorAll('.capability')].some(card=>!card.hidden);report.textContent=`匹配 ${n} / ${cards.length} 个接口`;}
search.addEventListener('input',filterCards);
document.querySelector('#expand-visible').addEventListener('click',()=>{for(const card of cards)if(!card.hidden)card.open=true;});
document.querySelector('#collapse-all').addEventListener('click',()=>{for(const card of cards)card.open=false;});
function openTarget(){const target=document.getElementById(decodeURIComponent(location.hash.slice(1)));if(target?.tagName==='DETAILS'){search.value='';filterCards();target.open=true;target.scrollIntoView();}}
window.addEventListener('hashchange',openTarget);openTarget();
if('IntersectionObserver'in window){const observer=new IntersectionObserver(entries=>{for(const entry of entries)if(entry.isIntersecting){for(const link of document.querySelectorAll('nav a'))link.classList.toggle('active',link.getAttribute('href')===`#${entry.target.id}`);}},{rootMargin:'-10% 0px -75% 0px'});for(const group of document.querySelectorAll('main>section'))observer.observe(group);}
