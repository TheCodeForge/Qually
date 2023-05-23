function csrf_token() {
      return $('#csrf-token-element').data('csrf-token');
}

//avoid console errors
$('a[href="javascript:void(0)').click(function(event){event.preventDefault()})


//textarea autoexpander

function autoExpand (field) {

  //get current scroll position
  xpos=window.scrollX;
  ypos=window.scrollY;

  // Reset field height
  field.style.height = 'inherit';

  // Get the computed styles for the element
  var computed = window.getComputedStyle(field);

  // Calculate the height
  var height = parseInt(computed.getPropertyValue('border-top-width'), 10)
  + parseInt(computed.getPropertyValue('padding-top'), 10)
  + field.scrollHeight
  + parseInt(computed.getPropertyValue('padding-bottom'), 10)
  + parseInt(computed.getPropertyValue('border-bottom-width'), 10)
  + 32;

  field.style.height = height + 'px';

  //keep window position from changing
  window.scrollTo(xpos,ypos);

};

document.addEventListener('input', function (event) {
  if (event.target.tagName.toLowerCase() !== 'textarea') return;
  autoExpand(event.target);
}, false);




//posty

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
  var approvals = $('#'+$(this).data('approvals-target'))
  postformtoast($(this), callback=function(xhr){
    //update displayed value
    target.html(JSON.parse(xhr.response)['new']);
    //visually clear approvals
    approvals.html('');
  })
});


//mobile prompt
if (("standalone" in window.navigator) &&       // Check if "standalone" property exists
    window.navigator.standalone){               // Test if using standalone navigator

    // Web page is loaded via app mode (full-screen mode)
    // (window.navigator.standalone is TRUE if user accesses website via App Mode)

} else {
  if (window.innerWidth <= 767){
    setTimeout(function(){
      $('#mobile-prompt').tooltip('show')
      $('.tooltip').click(function(event){
        $('#mobile-prompt').tooltip('hide');
        post('/dismiss_mobile_tooltip')

      })
    },
    1500
    )
  }
}

//iOS webapp stuff

(function(document, navigator, standalone) {
    // prevents links from apps from oppening in mobile safari
    // this javascript must be the first script in your <head>
    if ((standalone in navigator) && navigator[standalone]) {
        var curnode, location = document.location, stop = /^(a|html)$/i;
        document.addEventListener('click', function(e) {
            curnode = e.target;
            while (!(stop).test(curnode.nodeName)) {
                curnode = curnode.parentNode;
            }
            // Condidions to do this only on links to your own app
            // if you want all links, use if('href' in curnode) instead.
            if ('href'in curnode && (curnode.href.indexOf('http') || ~curnode.href.indexOf(location.host))) {
                e.preventDefault();
                location.href = curnode.href;
            }
        }, false);
    }
}
)(document, window.navigator, 'standalone');