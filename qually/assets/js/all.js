function csrf_token() {
      return $('#csrf-token-element').data('csrf-token');
}

//avoid console errors
$(document).on('click', 'a[href="javascript:void(0)"]', function(event){event.preventDefault()})

function post(url, callback=function(){}, errortext="") {
  var xhr = new XMLHttpRequest();
  xhr.open("POST", url, true);
  var form = new FormData()
  form.append("csrf_token", csrf_token());
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

function get(url, callback=function(){}, errortext="") {
  var xhr = new XMLHttpRequest();
  xhr.open("GET", url, true);
  xhr.withCredentials=true;
  xhr.onerror=function() { alert(errortext); };
  xhr.onload = function() {
    if (xhr.status >= 200 && xhr.status < 300) {
      callback();
    } else {
      xhr.onerror();
    }
  };
  xhr.send();
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
    $('.toast').toast('dispose')
    if (xhr.status >= 200 && xhr.status < 300) {
      $('#toast-success .toast-text').text(data['message']);
      $('#toast-success').toast('show');
    } else if (xhr.status >= 300 && xhr.status < 400 ) {
      window.location.href=data['redirect']
    } else {
      $('#toast-error .toast-text').text(data['error']);
      $('#toast-error').toast('show')
    }
    callback(xhr);
  };

  xhr.send(form);

  }

function post_reload(url) {
  var xhr = new XMLHttpRequest();
  xhr.open("POST", url, true);
  var form = new FormData()
  form.append("csrf_token", csrf_token());
  xhr.withCredentials=true;

  xhr.onload = function() {
    $('.toast').toast('dispose')
    if (xhr.status >= 200 && xhr.status < 300) {
      window.location.reload();
    } else if (xhr.status >= 300 && xhr.status < 400 ) {
      window.location.href=data['redirect']
    } else {
      $('#toast-error .toast-text').text("An error occurred");
      $('#toast-error').toast('show')
    }
    callback(xhr);
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
      $('#toast-error').toast('show');
  };
  xhr.onload = function() {
    data=JSON.parse(xhr.response);
    $('.toast').toast('dispose')
    if (xhr.status >= 200 && xhr.status < 300) {
      if (data['message']!=undefined) {
        $('#toast-success .toast-text').text(data['message']);
        $('#toast-success').toast('show');
      }
      if (x.hasClass('btn')) {
        x.prop('disabled', false);
        x.removeClass('disabled');
      }
      callback(xhr);
    } 
    else if (xhr.status >= 300 && xhr.status < 400 ) {
      if (x.hasClass('btn')) {
        x.prop('disabled', false);
        x.removeClass('disabled');
      }
      window.location.href=data['redirect']
    } 
    else if (xhr.status >=400 && xhr.status < 500) {
      $('#toast-error .toast-text').text(data['error']);
      $('#toast-error').toast('show')
      if (x.hasClass('btn')) {
        x.prop('disabled', false);
        x.removeClass('disabled');
      }
    } 
    else {
      $('#toast-error .toast-text').text("Something went wrong. Please try again later.");
      $('#toast-error').toast('show')
      if (x.hasClass('btn')) {
        x.prop('disabled', false);
        x.removeClass('disabled');
      }
    }
  };

  xhr.send(form);
  if (x.hasClass('btn')) {
    x.prop('disabled', true)
    x.addClass('disabled')
    $('#toast-waiting').toast('show')
  }
}


$('.toast-form-submit').click(function(){postformtoast($(this))});
$('.toast-form-change-submit').change(function(){postformtoast($(this))});

$(document).on('click', ".post-toast", function(){
  post_toast($(this).data('post-url'))
})

$(document).on('click', ".post-toast-reload", function(){
  post_reload($(this).data('post-url'))
})


//dark mode
$(".dark-switch").click(function(){
  post("/prefs/dark_mode", callback=function(){
    if ($('body').attr("data-bs-theme")=="light") {
      $('body').attr("data-bs-theme", "dark")
    } else {
      $('body').attr("data-bs-theme", "light")
    }
  })
})

$(".check-toast").click(function(){
  var btn=$(this);
  post_toast($(this).data('post-url'), callback=function(xhr){
    if (xhr.status>=400) {
      btn.prop("checked", !btn.prop("checked"))
    }
  })
})

//dismiss toasts when clicked on
$('.toast').click(function(){$('.toast').toast('dispose')})

//Login - check otp
$("#login-email").change(function(){

})

//let enter work with toasty forms
$("form.toasted input").keypress(function(e){
  if (e.which!=13) {
    return;
  }
  e.preventDefault();

  //click the thing with toast-form-submit and data-form=parent form id
  var form_id=$(this).parents("form").prop("id");
  $('.toast-form-submit[data-form="'+form_id+'"]').click()
})

$('.toggle-target-class').click(function(){
  $('.'+$(this).data('toggle-target')).toggleClass('d-none')
})

$('.record-value-edit').click(function(){
  var target = $('#'+$(this).data('value-target'))
  postformtoast($(this), callback=function(xhr){
    target.value(JSON.parse(xhr.response)['new'])
  })
});