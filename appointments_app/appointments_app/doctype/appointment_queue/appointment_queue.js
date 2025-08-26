// frappe.ui.form.on("Appointment Queue", {
// 	refresh(frm) {

// 	},
// });
frappe.ui.form.on('Appointment Queue', {
    refresh(frm) {
        hideGif();

        frm.fields_dict['send_to_hr'].input.addEventListener('change', function() {
            if (frm.doc.send_to_hr) {
                showGif(frm);
            } else {
                hideGif();
            }
        });
    },
});

function showGif(frm) {
    if (!document.getElementById('gifContainer')) {
        var gifContainer = document.createElement('div');
        gifContainer.id = 'gifContainer';

        gifContainer.innerHTML = '<img src="http://127.0.0.1:8000/files/unwatermark_Untitled(1).gif" alt="Click Action button and Send to HR.">';

        frm.fields_dict['send_to_hr'].$input.closest('.form-group').append(gifContainer);
    }

    document.getElementById('gifContainer').style.display = 'block';
}

function hideGif() {
    var gifContainer = document.getElementById('gifContainer');
    if (gifContainer) {
        gifContainer.style.display = 'none';
    }
}
