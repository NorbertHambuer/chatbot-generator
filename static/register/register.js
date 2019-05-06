function loginUser() {
    var username = $("#login_username").val();
    var password = $("#login_password").val();

    $.ajax({
        method: 'POST',
        url: 'login',
        data: {
            'username': username,
            'password': password
        },
        dataType: 'json',
        success: function (data) {
            //window.localStorage.setItem("jwt_token", data.access_token);
            //window.localStorage.setItem("refresh_token", data.refresh_token);
            console.log(data);
            window.location.href = 'home';
        }
    });
}

function registerUser() {
    var username = $("#register_username").val();
    var first_name = $("#register_first_name").val();
    var last_name = $("#register_last_name").val();
    var company = $("#register_company").val();
    var email = $("#register_email").val();
    var password = $("#register_password").val();
    var password_confirm = $("#register_password_confirm").val();

    if(password === password_confirm) {
        $.ajax({
            method: 'POST',
            url: 'register',
            data: {
                'username' : username,
                'first_name': first_name,
                'last_name': last_name,
                'email': email,
                'password': password,
                'company': company

            },
            dataType: 'json',
            success: function (data) {
                console.log(data);
                window.location.href = 'home';
            }
        });
    }else{
        alert("Password mismatch!");
    }
}

function resetPass() {
     var email = $("#lost_email").val();

    $.ajax({
        method: 'POST',
        url: '../reset_password/',
        data: {
            'email': email

        },
        dataType: 'json',
        success: function (data) {
            if (data.status == 1)
                console.log("Mail sent!");
            else
                console.log(data.message);
        }
    });
}

$(function () {
    var $formLogin = $('#login-form');
    var $formLost = $('#lost-form');
    var $formRegister = $('#register-form');
    var $divForms = $('#div-forms');
    var $modalAnimateTime = 300;
    var $msgAnimateTime = 150;
    var $msgShowTime = 2000;

    $('#login_register_btn').click(function () {
        modalAnimate($formLogin, $formRegister)
    });
    $('#register_login_btn').click(function () {
        modalAnimate($formRegister, $formLogin);
    });
    $('#login_lost_btn').click(function () {
        modalAnimate($formLogin, $formLost);
    });
    $('#lost_login_btn').click(function () {
        modalAnimate($formLost, $formLogin);
    });
    $('#lost_register_btn').click(function () {
        modalAnimate($formLost, $formRegister);
    });
    $('#register_lost_btn').click(function () {
        modalAnimate($formRegister, $formLost);
    });
    $('#login-modal').modal({backdrop: 'static', keyboard: false});

    function modalAnimate($oldForm, $newForm) {
        var $oldH = $oldForm.height();
        var $newH = $newForm.height();
        $divForms.css("height", $oldH);
        $oldForm.fadeToggle($modalAnimateTime, function () {
            $divForms.animate({height: $newH}, $modalAnimateTime, function () {
                $newForm.fadeToggle($modalAnimateTime);
            });
        });
    }

    function msgFade($msgId, $msgText) {
        $msgId.fadeOut($msgAnimateTime, function () {
            $(this).text($msgText).fadeIn($msgAnimateTime);
        });
    }

    function msgChange($divTag, $iconTag, $textTag, $divClass, $iconClass, $msgText) {
        var $msgOld = $divTag.text();
        msgFade($textTag, $msgText);
        $divTag.addClass($divClass);
        $iconTag.removeClass("glyphicon-chevron-right");
        $iconTag.addClass($iconClass + " " + $divClass);
        setTimeout(function () {
            msgFade($textTag, $msgOld);
            $divTag.removeClass($divClass);
            $iconTag.addClass("glyphicon-chevron-right");
            $iconTag.removeClass($iconClass + " " + $divClass);
        }, $msgShowTime);
    }

    /*$.ajaxSetup({
        beforeSend: function (xhr, settings) {

            xhr.setRequestHeader("X-CSRFToken", $("[name=csrfmiddlewaretoken]").val());

        }
    });*/
});

