/* ===================================================================
   PARALLAX — subtle image movement on scroll for the hero and the
   experience section. Disabled on touch-sized viewports and for
   people who've asked for reduced motion.
   =================================================================== */
(function(){
  var prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var heroImg = document.getElementById('heroImg');
  var expImg = document.getElementById('expImg');
  var experienceSection = document.querySelector('.experience');
  var ticking = false;

  function onScroll(){
    if (prefersReducedMotion || window.innerWidth <= 820) { ticking = false; return; }
    var y = window.scrollY;

    if (heroImg) {
      heroImg.style.transform = 'translateY(' + Math.min(y * 0.16, 130) + 'px) scale(1.1)';
    }
    if (expImg && experienceSection) {
      var rect = experienceSection.getBoundingClientRect();
      var vh = window.innerHeight;
      if (rect.bottom > 0 && rect.top < vh) {
        var progress = (vh - rect.top) / (vh + rect.height);
        expImg.style.transform = 'translateY(' + ((progress - 0.5) * 50) + 'px)';
      }
    }
    ticking = false;
  }
  window.addEventListener('scroll', function(){
    if (!ticking) { requestAnimationFrame(onScroll); ticking = true; }
  }, { passive: true });
  window.addEventListener('resize', onScroll);
  onScroll();
})();
