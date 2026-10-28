(function () {
  var btn = document.querySelector('.menu-btn');
  var body = document.body;
  if (!btn) return;
  function definir(aberto) {
    body.classList.toggle('menu-aberto', aberto);
    btn.setAttribute('aria-expanded', aberto ? 'true' : 'false');
  }
  btn.addEventListener('click', function () { definir(!body.classList.contains('menu-aberto')); });
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && body.classList.contains('menu-aberto')) { definir(false); btn.focus(); }
  });
  document.addEventListener('click', function (e) {
    if (body.classList.contains('menu-aberto') && !e.target.closest('.lateral-nav') && !e.target.closest('.menu-btn')) definir(false);
  });
})();

/* Menu lateral: Eixos abre ao passar o mouse (telas com mouse) e ao clicar */
(function(){
  var d=document.querySelector('.lnav__det');
  if(!d||!window.matchMedia)return;
  var hover=window.matchMedia('(hover:hover) and (min-width:901px)');
  var t;
  d.addEventListener('mouseenter',function(){if(!hover.matches)return;clearTimeout(t);d.open=true});
  d.addEventListener('mouseleave',function(){
    if(!hover.matches||d.hasAttribute('data-fixo'))return;
    t=setTimeout(function(){d.open=false},350);
  });
})();

/* Produtos: filtro por eixo */
(function(){
  var f=document.querySelector('.prod-filtro');
  if(!f)return;
  var cards=document.querySelectorAll('.prod[data-eixo]');
  f.addEventListener('click',function(e){
    var b=e.target.closest('button');if(!b)return;
    f.querySelectorAll('button').forEach(function(x){x.classList.toggle('ativo',x===b)});
    var v=b.getAttribute('data-eixo');
    cards.forEach(function(c){c.hidden=!!v&&c.getAttribute('data-eixo')!==v});
  });
})();

/* Galeria: visualização ampliada com setas e Esc */
(function(){
  var dlg=document.getElementById('lightbox');
  var links=[].slice.call(document.querySelectorAll('.gal-foto'));
  if(!dlg||!links.length||typeof dlg.showModal!=='function')return;
  var img=dlg.querySelector('img'),cap=dlg.querySelector('figcaption'),atual=0;
  function mostrar(i){
    atual=(i+links.length)%links.length;
    var a=links[atual];
    img.src=a.getAttribute('href');
    img.alt=a.getAttribute('data-legenda')||'';
    cap.textContent=a.getAttribute('data-legenda')||'';
  }
  links.forEach(function(a,i){a.addEventListener('click',function(e){e.preventDefault();mostrar(i);dlg.showModal()})});
  dlg.querySelector('.lightbox__fechar').addEventListener('click',function(){dlg.close()});
  dlg.querySelector('.lightbox__nav--ant').addEventListener('click',function(){mostrar(atual-1)});
  dlg.querySelector('.lightbox__nav--prox').addEventListener('click',function(){mostrar(atual+1)});
  dlg.addEventListener('keydown',function(e){
    if(e.key==='ArrowLeft')mostrar(atual-1);
    if(e.key==='ArrowRight')mostrar(atual+1);
  });
  dlg.addEventListener('click',function(e){if(e.target===dlg)dlg.close()});
})();
