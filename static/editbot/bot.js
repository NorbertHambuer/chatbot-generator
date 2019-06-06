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

    var formData = new FormData();

    formData.append('name', name);
    formData.append('knowledge', JSON.stringify(knowledge));

/*    formData.append('yml_files',$("#yml_files")[0]);
    formData.append('cml_files',$("#csv_files")[0]);*/
    for (let index = 0; index < $("#yml_files")[0].files.length; index++)
        formData.append('yml_files', $("#yml_files")[0].files[index]);

    for (let index = 0; index < $("#csv_files")[0].files.length; index++)
        formData.append('csv_files', $("#csv_files")[0].files[index]);

    $.ajax({
        method: 'POST',
        url: 'create_bot',
        data: formData,
        dataType: 'json',
        cache: false,
        contentType: false,
        processData: false,
        beforeSend: function (xhr) {   //Include the bearer token in header
            xhr.setRequestHeader("X-CSRF-TOKEN", getCookie("csrf_access_token"));
        },
        success: function (data) {
            //window.location.href = 'home';
        },
        error: function (error) {
            console.log(error);
        }
    });
}
