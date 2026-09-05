/* ===================================================================
   ANIMATIONS — the one orchestrated hero entrance, plus the sparing
   reveal-on-scroll effect used on [data-reveal] elements (About image,
   Experience section).
   =================================================================== */
(function(){
  var prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* Single orchestrated hero entrance */
  function markLoaded(){ document.body.classList.add('is-loaded'); }
  if (document.readyState === 'complete') { requestAnimationFrame(markLoaded); }
  else { window.addEventListener('load', function(){ requestAnimationFrame(markLoaded); } ); }
  setTimeout(markLoaded, 1200); /* fallback if load is slow */

  /* Reveal — used sparingly, only on elements explicitly marked [data-reveal] */
  var revealEls = document.querySelectorAll('[data-reveal]');
  if (prefersReducedMotion || !('IntersectionObserver' in window)) {
    revealEls.forEach(function(el){ el.classList.add('is-visible'); });
  } else {
    var revealObserver = new IntersectionObserver(function(entries, obs){
      entries.forEach(function(entry){
        if (entry.isIntersecting) {
          entry.target.classList.add('is-visible');
          obs.unobserve(entry.target);
        }
      });
    }, { threshold: 0.2 });
    revealEls.forEach(function(el){ revealObserver.observe(el); });
  }
})();
