var knowledge_selector = new SelectBeauty({
    el: '#predefined_knowledge',
    length: 5,
    max: 10
});

function getCookie(name) {
  var value = "; " + document.cookie;
  var parts = value.split("; " + name + "=");
  if (parts.length == 2) return parts.pop().split(";").shift();
}

function create_bot() {
   let name = $("#name").val();
   let knowledge = Object.keys(this.knowledge_selector.selected).map(function (key, index) {
       return key;
   });

   $.ajax({
       method: 'POST',
       url: 'create_bot',
       data: {
           'name': name,
           'knowledge': JSON.stringify(knowledge)
       },
       dataType: 'json',
       beforeSend: function (xhr) {   //Include the bearer token in header
           xhr.setRequestHeader("X-CSRF-TOKEN", getCookie("csrf_access_token"));
       },
       success: function (data) {
           window.location.href = 'home';
       },
       error: function (error) {
           console.log(error);
       }
   });
}
