(function() {

function redirectToArchive(e) {
  if (!e.target.value)
    return;

  window.location.href = '/archive/' + e.target.value;
}

window.addEventListener('load', function() {
  var selector = document.getElementById('select_archive');
  selector.addEventListener('change', redirectToArchive);
});

})()