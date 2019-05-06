function modalConfirm(callback, container, title, message, trueText, falseText) {
    $(`#${container}`).modal('show');

    $(`#${container} #modal-confirm-title`).html(title);
    $(`#${container} #modal-confirm-body`).html(message);
    $(`#${container} #modal-confirm-yes`).html(trueText);
    $(`#${container} #modal-confirm-no`).html(falseText);

    let handler_yes = function () {
        callback(true);
        $(`#${container}`).modal('hide');
    };

    let handler_no = function () {
        callback(false);
        $(`#${container}`).modal('hide');
    };

    $(`#${container} #modal-confirm-yes`).on("click", function () {
        handler_yes();
        $("#modal-confirm-yes").off();
        $("#modal-confirm-no").off();
    });

    $(`#${container} #modal-confirm-no`).on("click", function () {
        handler_no();
        $("#modal-confirm-no").off();
        $("#modal-confirm-yes").off();
    });
};