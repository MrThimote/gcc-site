/* Copyright (C) <2018> Association Prologin <association@prologin.org>
 * SPDX-License-Identifier: GPL-3.0+
 */
const applicants = document.getElementsByClassName('applicant-head');

function goToApplicant(applicant) {
    // Unfold an applicant's description, and scroll down toward its position
    applicant.show();

    // Scroll to get out of the header
    setTimeout(function() {
        $([document.documentElement, document.body]).animate({
            scrollTop: $(applicant.prev()).offset().top
        }, 0);
    }, 1);
}

/**
 * If there is an anchor to the page, open corresponding applicant and scroll
 * to it.
 */
const url_parts = document.URL.split('#');

if (url_parts.length > 1) {
    const focused_id = url_parts[1];
    const focused_el = $('#' + focused_id);
    goToApplicant(focused_el.next());
}

/**
 * Swap the active status when clicking on an applicant
 */
for (let i = 0 ; i < applicants.length ; i++) {
    applicants[i].addEventListener('click', (event) => {
        const applicant = $(applicants[i]).next();
        applicant.toggle();
    });
}

/**
 * Close all details when hitting escape
 */
document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape')
        for (let i = 0 ; i < applicants.length ; i++)
            $(applicants[i]).next().hide();
});

/**
 * Select next item when pressing `down` arrow
 */
document.addEventListener('keydown', (event) => {
    if (event.key === 'ArrowDown') {
        event.preventDefault();

        let last_opened = -1;

        for (let i = 0 ; i < applicants.length ; i++)
            if ($(applicants[i]).next().is(':visible'))
                last_opened = i;

        if (last_opened != -1)
            $(applicants[last_opened]).next().hide();
        if (last_opened != applicants.length - 1)
            goToApplicant($(applicants[last_opened + 1]).next());
    }
});

/**
 * Select previous item when pressing `up` arrow
 */
document.addEventListener('keydown', (event) => {
    if (event.key === 'ArrowUp') {
        event.preventDefault();

        let last_opened = applicants.length;

        for (let i = applicants.length-1 ; i >= 0 ; i--)
            if ($(applicants[i]).next().is(':visible'))
                last_opened = i;

        if (last_opened != applicants.length)
            $(applicants[last_opened]).next().hide();
        if (last_opened != 0)
            goToApplicant($(applicants[last_opened - 1]).next());
    }
});

/**
 * Enable dropdowns
 */
$('.dropdown-toggle').on('click', function(event) {
    $(`.dropdown-menu[aria-labelledby="${event.target.id}"]`).toggle();
});

/**
 * Handle labels
 */

$('.remove-label').on('click', function (event) {
    event.stopPropagation();

    const applicant_id = $(event.target).attr('for-applicant');
    const event_id = $(event.target).attr('for-event');
    const label_id = $(event.target).attr('for-label');
    const url = `/application/label_remove/${event_id}/${applicant_id}/${label_id}`;

    $.getJSON(url, function(data) {
        if (data['status'] == 'ok') {
            $(`.label[for-applicant=${applicant_id}][for-label=${label_id}][for-event=${event_id}]`).hide();
            $(`.add-label[for-applicant=${applicant_id}][for-label=${label_id}][for-event=${event_id}]`).show();
        }
        else {
            console.error('error:', data);
        }
    })
})

$('.add-label').on('click', function (event) {
    event.stopPropagation();

    const applicant_id = $(event.target).attr('for-applicant');
    const event_id = $(event.target).attr('for-event');
    const label_id = $(event.target).attr('for-label');
    const url = `/application/label_add/${event_id}/${applicant_id}/${label_id}`;

    $.getJSON(url, function(data) {
        if (data['status'] == 'ok') {
            $(`.label[for-applicant=${applicant_id}][for-label=${label_id}][for-event=${event_id}]`).show();
            $(`.add-label[for-applicant=${applicant_id}][for-label=${label_id}][for-event=${event_id}]`).hide();
        }
        else {
            console.error('error:', data);
        }
    })
})

/**
 * Handle wish updates
 */
$('.update-wish').on('click', function (event) {
    event.stopPropagation();

    const wish_id = $(event.target).attr('for-wish');
    const new_status = $(event.target).attr('new-status');
    const url = `/application/update_wish/${wish_id}/${new_status}/`;

    $.getJSON(url, function(data) {
        if (data['status'] == 'ok') {
            const applicant = data['applicant'];
            const elem = $(`#wish-${wish_id}`);
            elem.find('.update-wish').hide();

            // Update buttons
            // If it's gonna pending, show select & reject
            if (new_status == 1)
            {
                elem.find('.update-wish[new-status="2"]').show();
                elem.find('.update-wish[new-status="3"]').show();
            }
            // If it's gonna be accepted, show confirm & cancel (that redirects to pending)
            else if (new_status == 4)
            {
                elem.find('.update-wish[new-status="1"]').show();
                elem.find('.update-wish[new-status="5"]').show();
            }
            // If it's gonna be anything but pending/confirmed, show cancel (that redirects to pending)
            else
                elem.find('.update-wish[new-status="4"]').show();

            // Update badge
            elem.find('.badge').hide();
            elem.find(`.badge[status=${new_status}]`).show();

            // Update applicant status
            $(`#applicant-${applicant} .applicant-status`).text(data['applicant-status']);

            // Update acceptables counter
            $(".acceptables-counter").text(data['nb_acceptable_applicants']);
        }
        else {
            console.error('error:', data);
        }
    })
})

