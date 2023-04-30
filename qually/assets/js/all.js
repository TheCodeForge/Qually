function csrf_token() {
      return $('#csrf-token-element').data('csrf-token');
}

function post(url, callback=function(){}, errortext="") {
  var xhr = new XMLHttpRequest();
  xhr.open("POST", url, true);
  var form = new FormData()
  form.append("formkey", formkey());
  xhr.withCredentials=true;
  xhr.onerror=function() { alert(errortext); };
  xhr.onload = function() {
    if (xhr.status >= 200 && xhr.status < 300) {
      callback();
    } else {
      xhr.onerror();
    }
  };
  xhr.send(form);
};

function post_toast(url, callback=function(xhr){}) {
  var xhr = new XMLHttpRequest();
  xhr.open("POST", url, true);
  var form = new FormData()
  form.append("csrf_token", csrf_token());
  xhr.withCredentials=true;

  xhr.onload = function() {
    if (xhr.status==204){
      return
    }
    data=JSON.parse(xhr.response);
    if (xhr.status >= 200 && xhr.status < 300) {
      $('#toast-success .toast-text').text(data['message']);
      $('#toast-success').toast('show');
      callback(xhr);
    } else if (xhr.status >= 300 && xhr.status < 400 ) {
      window.location.href=data['redirect']
    } else {
      $('#toast-error .toast-text').text(data['error']);
      $('#toast-error').toast('show')
    }
  };

  xhr.send(form);

  }

function postformtoast(x, callback=function(data){}){

  var form_id
  if (x.prop('tagName')=='FORM') {
    form_id=x.prop('id')
  }
  else {
    form_id=x.data('form')
  }

  var xhr = new XMLHttpRequest();
  var url=$('#'+form_id).prop('action');
  var method=$('#'+form_id).prop('method')

  xhr.open("POST", url, true);
  var form = new FormData($('#'+form_id)[0]);
  xhr.withCredentials=true;
  xhr.onerror=function() { 
      $('#toast-error .toast-text').text("Something went wrong. Please try again later.");
      $('#toast-error').toast('show')
  };
  xhr.onload = function() {
    data=JSON.parse(xhr.response);
    if (xhr.status >= 200 && xhr.status < 300) {
      if (data['message']!=undefined) {
        $('#toast-success .toast-text').text(data['message']);
        $('#toast-success').toast('show');
        x.text(x.data('text'))
      }
      if (x.hasClass('btn')) {
        x.prop('disabled', false)
        x.removeClass('disabled')
        x.text(x.data('text'))
      }
      callback(xhr);
    } 
    else if (xhr.status >= 300 && xhr.status < 400 ) {
      if (x.hasClass('btn')) {
        x.prop('disabled', false)
        x.removeClass('disabled')
        x.text(x.data('text'))
      }
      window.location.href=data['redirect']
    } 
    else if (xhr.status >=400 && xhr.status < 500) {
      $('#toast-error .toast-text').text(data['error']);
      $('#toast-error').toast('show')
      if (x.hasClass('btn')) {
        x.prop('disabled', false)
        x.removeClass('disabled')
        x.text(x.data('text'))
      }
    } 
    else {
      $('#toast-error .toast-text').text("Something went wrong. Please try again later.");
      $('#toast-error').toast('show')
      if (x.hasClass('btn')) {
        x.prop('disabled', false)
        x.removeClass('disabled')
        x.text(x.data('text'))
      }
    }
  };

  xhr.send(form);
  if (x.hasClass('btn')) {
    x.prop('disabled', true)
    x.width(x.width()); //pins width at whatever the current value is
    x.data('text', x.text())
    x.addClass('disabled')
    x.html('<i class="fas fa-circle-notch fa-spin"></i>')
  }
}


$('.toast-form-submit').click(function(){postformtoast($(this))});
$('.toast-form-change-submit').change(function(){postformtoast($(this))});

$(document).on('click', ".post-toast", function(){
  post_toast($(this).data('post-url'))
})


//dark mode
$(".dark-switch").click(function(){
  if ($('body').attr("data-bs-theme")=="light") {
    $('body').attr("data-bs-theme", "dark")
  } else {
    $('body').attr("data-bs-theme", "light")
  }
})