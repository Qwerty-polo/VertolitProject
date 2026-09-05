/* ===================================================================
   MISC — small, one-off site utilities that don't warrant their own
   file. Currently just the footer copyright year.
   =================================================================== */
(function(){
  var yearEl = document.getElementById('year');
  if (yearEl) yearEl.textContent = new Date().getFullYear();
})();
