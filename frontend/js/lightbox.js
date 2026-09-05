/* ===================================================================
   LIGHTBOX — full-screen photo viewer opened by clicking a gallery
   photo. Supports prev/next buttons, click-outside-to-close, and
   arrow-key / Escape navigation.
   =================================================================== */
(function(){
  var triggers = Array.prototype.slice.call(document.querySelectorAll('.gallery-trigger'));
  var scrollTrack = document.getElementById('galleryScroll');
  var lightbox = document.getElementById('lightbox');
  var lightboxImg = document.getElementById('lightboxImg');
  var lightboxCaption = document.getElementById('lightboxCaption');
  var currentIndex = 0;

  if (!lightbox || !triggers.length) return;

  function updateLightbox(){
    var el = triggers[currentIndex];
    var img = el.querySelector('img');
    lightboxImg.src = img.src;
    lightboxImg.alt = img.alt;
    lightboxCaption.textContent = el.dataset.caption || '';
  }
  function openLightbox(i){
    currentIndex = i;
    updateLightbox();
    lightbox.classList.add('is-open');
    lightbox.setAttribute('aria-hidden', 'false');
    document.body.classList.add('no-scroll');
  }
  function closeLightbox(){
    lightbox.classList.remove('is-open');
    lightbox.setAttribute('aria-hidden', 'true');
    document.body.classList.remove('no-scroll');
  }

  triggers.forEach(function(el, i){
    el.addEventListener('click', function(){
      /* Ignore the click that ends a filmstrip drag */
      if (scrollTrack && scrollTrack.classList.contains('is-dragging')) return;
      openLightbox(i);
    });
  });
  document.getElementById('lightboxClose').addEventListener('click', closeLightbox);
  document.getElementById('lightboxPrev').addEventListener('click', function(){
    currentIndex = (currentIndex - 1 + triggers.length) % triggers.length;
    updateLightbox();
  });
  document.getElementById('lightboxNext').addEventListener('click', function(){
    currentIndex = (currentIndex + 1) % triggers.length;
    updateLightbox();
  });
  lightbox.addEventListener('click', function(e){ if (e.target === lightbox) closeLightbox(); });
  document.addEventListener('keydown', function(e){
    if (!lightbox.classList.contains('is-open')) return;
    if (e.key === 'Escape') closeLightbox();
    if (e.key === 'ArrowRight') document.getElementById('lightboxNext').click();
    if (e.key === 'ArrowLeft') document.getElementById('lightboxPrev').click();
  });
})();
