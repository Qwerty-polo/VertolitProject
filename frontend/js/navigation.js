/* ===================================================================
   NAVIGATION — navbar background on scroll, active link tracking,
   and the mobile menu overlay.
   =================================================================== */
(function(){
  var navbar = document.getElementById('navbar');
  var ticking = false;

  function onScroll(){
    navbar.classList.toggle('is-scrolled', window.scrollY > 60);
    ticking = false;
  }
  window.addEventListener('scroll', function(){
    if (!ticking) { requestAnimationFrame(onScroll); ticking = true; }
  }, { passive: true });
  onScroll();

  /* Active nav link tracks scroll position */
  var navLinks = document.querySelectorAll('.navbar__link');
  var sections = document.querySelectorAll('#home, #about, #services, #gallery, #contacts');
  if ('IntersectionObserver' in window && sections.length) {
    var sectionObserver = new IntersectionObserver(function(entries){
      entries.forEach(function(entry){
        if (entry.isIntersecting) {
          navLinks.forEach(function(l){ l.classList.remove('is-active'); });
          var match = document.querySelector('.navbar__link[href="#' + entry.target.id + '"]');
          if (match) match.classList.add('is-active');
        }
      });
    }, { rootMargin: '-45% 0px -50% 0px' });
    sections.forEach(function(s){ sectionObserver.observe(s); });
  }

  /* Mobile nav */
  var navToggle = document.getElementById('navToggle');
  var mobileNav = document.getElementById('mobileNav');
  function closeMobileNav(){
    navToggle.setAttribute('aria-expanded', 'false');
    mobileNav.classList.remove('is-open');
    mobileNav.setAttribute('aria-hidden', 'true');
    document.body.classList.remove('no-scroll');
  }
  if (navToggle && mobileNav) {
    navToggle.addEventListener('click', function(){
      var willOpen = !mobileNav.classList.contains('is-open');
      navToggle.setAttribute('aria-expanded', String(willOpen));
      mobileNav.classList.toggle('is-open', willOpen);
      mobileNav.setAttribute('aria-hidden', String(!willOpen));
      document.body.classList.toggle('no-scroll', willOpen);
    });
    mobileNav.querySelectorAll('a').forEach(function(a){ a.addEventListener('click', closeMobileNav); });
  }
})();
