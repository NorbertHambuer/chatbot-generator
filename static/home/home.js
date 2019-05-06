function getCookie(name) {
  var value = "; " + document.cookie;
  var parts = value.split("; " + name + "=");
  if (parts.length == 2) return parts.pop().split(";").shift();
}

function get_response() {
   let question = $("#question").val();

   $.ajax({
       method: 'GET',
       url: 'get_response?bot_name=Ben&user_id=2&question='+question,
       dataType: 'json',
       beforeSend: function (xhr) {   //Include the bearer token in header
           xhr.setRequestHeader("X-CSRF-TOKEN", getCookie("csrf_access_token"));
       },
       success: function (data) {
           console.log(data);
       },
       error: function (error) {
           console.log(error);
       }
   });
}
