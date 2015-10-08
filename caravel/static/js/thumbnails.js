var removeThumbnail = function(button, id) {
  var thumbnail = button.parentNode.parentNode;
  var upload = document.getElementById(id);
  upload.type = 'file';
  thumbnail.parentNode.replaceChild(upload, thumbnail);
};