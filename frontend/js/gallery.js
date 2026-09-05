/* ===================================================================
   GALLERY — the "Дивитись" cursor that follows the pointer over
   photos, plus desktop drag-to-scroll and the arrow buttons for the
   horizontal filmstrip. Touch devices keep native scrolling.
   =================================================================== */
(function(){
  var prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var hasFinePointer = window.matchMedia('(pointer: fine)').matches;

  /* Custom cursor — appears only over gallery photos, fine pointer only */
  var cursorDot = document.getElementById('cursorDot');
  if (hasFinePointer && !prefersReducedMotion && cursorDot) {
    var mx = 0, my = 0, cx = 0, cy = 0;
    window.addEventListener('mousemove', function(e){ mx = e.clientX; my = e.clientY; });
    function cursorLoop(){
      cx += (mx - cx) * 0.18;
      cy += (my - cy) * 0.18;
      cursorDot.style.transform = 'translate(' + (cx - cursorDot.offsetWidth/2) + 'px,' + (cy - cursorDot.offsetHeight/2) + 'px)';
      requestAnimationFrame(cursorLoop);
    }
    requestAnimationFrame(cursorLoop);
    document.querySelectorAll('.gallery-trigger').forEach(function(el){
      el.addEventListener('mouseenter', function(){
        cursorDot.classList.add('is-visible', 'is-active');
        cursorDot.textContent = 'Дивитись';
      });
      el.addEventListener('mouseleave', function(){
        cursorDot.classList.remove('is-visible', 'is-active');
        cursorDot.textContent = '';
      });
    });
  }

  /* Gallery: desktop drag-to-scroll (touch keeps native scrolling) + arrow buttons */
  var scrollTrack = document.getElementById('galleryScroll');
  if (scrollTrack) {
    var isDown = false, startX = 0, startScroll = 0, dragged = false;
    scrollTrack.addEventListener('pointerdown', function(e){
      if (e.pointerType !== 'mouse') return;
      isDown = true; dragged = false;
      startX = e.clientX; startScroll = scrollTrack.scrollLeft;
      scrollTrack.classList.add('is-dragging');
    });
    window.addEventListener('pointermove', function(e){
      if (!isDown) return;
      var dx = e.clientX - startX;
      if (Math.abs(dx) > 4) dragged = true;
      scrollTrack.scrollLeft = startScroll - dx;
    });
    window.addEventListener('pointerup', function(){
      isDown = false;
      scrollTrack.classList.remove('is-dragging');
    });
    scrollTrack.addEventListener('click', function(e){
      if (dragged) { e.preventDefault(); e.stopPropagation(); dragged = false; }
    }, true);
    document.querySelectorAll('.scroll-btn').forEach(function(btn){
      btn.addEventListener('click', function(){
        scrollTrack.scrollBy({ left: Number(btn.dataset.dir) * 380, behavior: 'smooth' });
      });
    });
  }
})();
